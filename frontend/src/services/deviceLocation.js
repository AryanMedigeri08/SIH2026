export function getDevicePosition(geolocation = globalThis.navigator?.geolocation) {
  if (!geolocation) return Promise.reject(new Error('Location is unavailable on this device. Choose the business location manually.'));
  return new Promise((resolve, reject) => {
    const success = position => resolve({latitude:position.coords.latitude,longitude:position.coords.longitude,accuracy:position.coords.accuracy});
    const failure = error => reject(new Error(error.code===1
      ? 'Location access is blocked. Allow location for this site in your browser, then retry, or choose the business location manually.'
      : 'The device could not determine your location. Retry near a window or choose the business location manually.'));
    geolocation.getCurrentPosition(success, error => {
      if (error.code===1) failure(error);
      else geolocation.getCurrentPosition(success,failure,{enableHighAccuracy:false,timeout:10000,maximumAge:60000});
    },{enableHighAccuracy:true,timeout:12000,maximumAge:60000});
  });
}
