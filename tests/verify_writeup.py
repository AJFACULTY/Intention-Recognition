import os
import re

chapters = ['ch1_introduction.tex', 'ch2_literature_review.tex', 'ch3_methodology.tex', 'ch4_results.tex', 'ch5_conclusion.tex']
bib_path = 'write_up/references.bib'
figures_dir = 'write_up/figures'

with open(bib_path) as f:
    bib_content = f.read()
bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib_content))
print(f'Loaded {len(bib_keys)} bibliography keys.')

figures = set(os.listdir(figures_dir))
print(f'Found {len(figures)} figures in {figures_dir}.')

all_labels = set()
all_refs = []
all_cites = []
all_graphics = []
mismatches = False

for ch in chapters:
    path = os.path.join('write_up/chapters', ch)
    with open(path) as f:
        content = f.read()
    
    # Stack-based environment check
    env_pattern = re.compile(r'\\(begin|end)\{([^}]+)\}')
    stack = []
    env_error = False
    for match in env_pattern.finditer(content):
        action, env = match.groups()
        if action == 'begin':
            stack.append(env)
        elif action == 'end':
            if not stack:
                print(f'UNEXPECTED END: \\end{{{env}}} in {ch}')
                env_error = True
            else:
                top = stack.pop()
                if top != env:
                    print(f'ENV MISMATCH in {ch}: expected \\end{{{top}}}, found \\end{{{env}}}')
                    env_error = True
    if stack:
        print(f'UNCLOSED ENVS in {ch}: {stack}')
        env_error = True
    if not env_error:
        print(f'{ch}: Environments properly nested and closed')
        
    labels = re.findall(r'\\label\{([^}]+)\}', content)
    all_labels.update(labels)
    refs = re.findall(r'\\ref\{([^}]+)\}', content)
    all_refs.extend([(r, ch) for r in refs])
    cites = re.findall(r'\\cite\{([^}]+)\}', content)
    for c in cites:
        for k in c.split(','):
            all_cites.append((k.strip(), ch))
    gfx = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', content)
    all_graphics.extend([(g, ch) for g in gfx])

print('\n--- Checking Figures ---')
missing_figs = False
for g, ch in all_graphics:
    base = os.path.basename(g)
    if base not in figures:
        print(f'  [MISSING FIGURE]: {g} referenced in {ch}')
        missing_figs = True
    else:
        print(f'  [OK] Figure: {g} in {ch}')

print('\n--- Checking Citations ---')
missing_cites = False
for c, ch in all_cites:
    if c not in bib_keys:
        print(f'  [MISSING CITE]: {c} referenced in {ch}')
        missing_cites = True
    else:
        print(f'  [OK] Citation: {c} in {ch}')

print('\n--- Checking References ---')
missing_refs = False
for r, ch in all_refs:
    if r not in all_labels:
        print(f'  [MISSING LABEL for ref]: {r} in {ch}')
        missing_refs = True
    else:
        print(f'  [OK] Ref: {r} in {ch}')

print('\n--- Checking Paragraph Sentence Counts (GCTU Rule: >= 3 sentences) ---')

def count_sentences(text):
    clean = re.sub(r'\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^\}]*\})*', ' ', text)
    clean = re.sub(r'[\{\}\$]', ' ', clean)
    clean = clean.replace('~', ' ')
    sentences = re.split(r'[.!?]+(?:\s+|$)', clean.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    return len(sentences)

ignored_envs = {'figure', 'figure*', 'table', 'table*', 'longtable', 'tabular', 'lstlisting', 'verbatim', 'equation', 'equation*', 'align', 'align*', 'gather', 'center', 'landscape'}

for ch in chapters:
    path = os.path.join('write_up/chapters', ch)
    with open(path) as f:
        lines = f.readlines()
    
    paras = []
    curr = []
    in_ignored = 0
    for line in lines:
        stripped = line.strip()
        
        # Track environments
        begin_match = re.match(r'\\begin\{([^}]+)\}', stripped)
        if begin_match:
            if curr:
                paras.append(' '.join(curr))
                curr = []
            env_name = begin_match.group(1)
            if env_name in ignored_envs:
                in_ignored += 1
            continue
            
        end_match = re.match(r'\\end\{([^}]+)\}', stripped)
        if end_match:
            if curr:
                paras.append(' '.join(curr))
                curr = []
            env_name = end_match.group(1)
            if env_name in ignored_envs:
                in_ignored = max(0, in_ignored - 1)
            continue
            
        if in_ignored > 0:
            continue
            
        if stripped.startswith('\\') and any(stripped.startswith(k) for k in ['\\chapter', '\\section', '\\subsection', '\\subsubsection', '\\paragraph']):
            if curr:
                paras.append(' '.join(curr))
                curr = []
            continue
            
        if stripped.startswith(('\\centering', '\\footnotesize', '\\normalsize', '\\hfill', '\\clearpage', '\\pagebreak', '\\vspace', '\\hspace', '\\addcontentsline')):
            continue
            
        if not stripped:
            if curr:
                paras.append(' '.join(curr))
                curr = []
        else:
            curr.append(stripped)
    if curr:
        paras.append(' '.join(curr))
    
    short_paras = []
    for i, p in enumerate(paras):
        if p.startswith('\\item') or p.startswith('\\caption') or p.startswith('\\includegraphics') or p.startswith('\\label') or p.startswith('\\hline'):
            continue
        cnt = count_sentences(p)
        if cnt < 3:
            short_paras.append((i+1, cnt, p[:60]))
            
    if short_paras:
        print(f'{ch}: {len(short_paras)} paragraphs with < 3 sentences:')
        for idx, cnt, snippet in short_paras:
            print(f'   Para {idx} ({cnt} sents): {snippet}...')
    else:
        print(f'{ch}: All paragraphs satisfy GCTU rule (>= 3 sentences) [PASS]')

if not (missing_figs or missing_cites or missing_refs or mismatches):
    print('\n======================================================')
    print('>>> ALL FIGURES, CITATIONS, LABELS & ENVS VERIFIED! <<<')
    print('======================================================')
