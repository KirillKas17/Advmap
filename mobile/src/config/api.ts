/**Конфигурация API.*/
export const API_CONFIG = {
  BASE_URL: __DEV__
    ? 'http://localhost:8000/api/v1'
    : 'https://api.travelgame.com/api/v1',
  TIMEOUT: 30000,
};

export const ENDPOINTS = {
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    ME: '/auth/me',
  },
  LOCATION: {
    SESSION: '/location/session',
    POINT: '/location/session/:sessionId/point',
    OFFLINE_SYNC: '/location/offline/sync',
    BATCH_SYNC: '/location/offline/batch-sync',
    POINTS: '/location/points',
    LAST: '/location/last',
  },
  GEOZONE: {
    CREATE: '/geozone',
    LIST: '/geozone',
    DETAIL: '/geozone/:id',
    CHECK: '/geozone/:id/check',
    CHECK_NEARBY: '/geozone/check-nearby',
    VISITS: '/geozone/visits/my',
  },
  ACHIEVEMENT: {
    MY: '/achievement/my',
    CHECK: '/achievement/check',
  },
  HOME_WORK: {
    LIST: '/home-work',
    ANALYZE: '/home-work/analyze',
  },
};
