const robotHost = (window.location.protocol === 'file:') ? 'localhost' : (window.location.hostname || 'localhost');

const CONFIG = {
  rosbridgeUrl:   `ws://${robotHost}:9090`,
  videoStreamUrl: `http://${robotHost}:8080/stream?topic=/camera/image_raw/compressed&quality=60&width=320`,
  cameraTopic:    '/camera/image_raw/compressed',
  domainId:       20,
  buildTarget:    'robot',
  envLabel:       'Physical Robot (Pi 5)'
};
