export const TARGET = Object.freeze({cluster: 'lab', namespace: 'staging', name: 'checkout'});
export const RESTART_PATH = '/api/deployments/' + TARGET.namespace + '/' + TARGET.name + '/restart';
