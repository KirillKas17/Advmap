/**Сервис для работы с геолокацией.*/
import BackgroundGeolocation, {
  Location,
  State,
  Config,
} from 'react-native-background-geolocation';
import Geolocation from '@react-native-community/geolocation';

import {apiService} from './api';
import {ENDPOINTS} from '../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface LocationPoint {
  latitude: number;
  longitude: number;
  accuracy_meters?: number;
  altitude_meters?: number;
  speed_ms?: number;
  heading_degrees?: number;
  timestamp: string;
}

class LocationService {
  private currentSessionId: number | null = null;
  private offlinePoints: LocationPoint[] = [];
  private isOnline: boolean = true;

  constructor() {
    this.setupBackgroundGeolocation();
    this.setupOfflineSync();
  }

  private async setupBackgroundGeolocation(): Promise<void> {
    const config: Config = {
      desiredAccuracy: BackgroundGeolocation.DESIRED_ACCURACY_HIGH,
      distanceFilter: 10,
      stopTimeout: 5,
      debug: __DEV__,
      logLevel: __DEV__
        ? BackgroundGeolocation.LOG_LEVEL_VERBOSE
        : BackgroundGeolocation.LOG_LEVEL_OFF,
      stopOnTerminate: false,
      startOnBoot: true,
      enableHeadless: true,
      url: '',
      autoSync: true,
      autoSyncThreshold: 10,
      batchSync: false,
      maxBatchSize: 50,
      maxDaysToPersist: 7,
    };

    await BackgroundGeolocation.ready(config);

    // Обработчик событий геолокации
    BackgroundGeolocation.onLocation(
      this.handleLocationUpdate.bind(this),
      error => {
        console.error('[LocationService] Location error:', error);
      },
    );

    // Обработчик изменения состояния
    BackgroundGeolocation.onMotionChange(event => {
      console.log('[LocationService] Motion change:', event.isMoving, event.location);
    });

    // Обработчик изменения активности
    BackgroundGeolocation.onActivityChange(event => {
      console.log('[LocationService] Activity change:', event.activity);
    });
  }

  private async handleLocationUpdate(location: Location): Promise<void> {
    const point: LocationPoint = {
      latitude: location.coords.latitude,
      longitude: location.coords.longitude,
      accuracy_meters: location.coords.accuracy,
      altitude_meters: location.coords.altitude,
      speed_ms: location.coords.speed,
      heading_degrees: location.coords.heading,
      timestamp: new Date(location.timestamp).toISOString(),
    };

    if (this.isOnline && this.currentSessionId) {
      try {
        await apiService.post(
          ENDPOINTS.LOCATION.POINT.replace(':sessionId', this.currentSessionId.toString()),
          point,
        );
      } catch (error) {
        console.error('[LocationService] Failed to send location:', error);
        // Сохранить в офлайн хранилище
        this.offlinePoints.push(point);
        this.isOnline = false;
      }
    } else {
      // Сохранить в офлайн хранилище
      this.offlinePoints.push(point);
    }
  }

  private async setupOfflineSync(): Promise<void> {
    // Периодическая синхронизация офлайн данных
    setInterval(async () => {
      if (this.offlinePoints.length > 0 && this.isOnline) {
        await this.syncOfflineData();
      }
    }, 60000); // Каждую минуту
  }

  async startTracking(): Promise<void> {
    const state: State = await BackgroundGeolocation.getState();
    if (!state.enabled) {
      await BackgroundGeolocation.start();
    }

    // Создать сессию
    try {
      const session = await apiService.post(ENDPOINTS.LOCATION.SESSION, {
        is_background: true,
        is_offline: false,
      });
      this.currentSessionId = session.id;
      await AsyncStorage.setItem('current_session_id', session.id.toString());
    } catch (error) {
      console.error('[LocationService] Failed to create session:', error);
      // Продолжить работу в офлайн режиме
      this.isOnline = false;
    }
  }

  async stopTracking(): Promise<void> {
    await BackgroundGeolocation.stop();
    this.currentSessionId = null;
    await AsyncStorage.removeItem('current_session_id');
  }

  async syncOfflineData(): Promise<void> {
    if (this.offlinePoints.length === 0) {
      return;
    }

    try {
      const points = [...this.offlinePoints];
      this.offlinePoints = [];

      await apiService.post(ENDPOINTS.LOCATION.OFFLINE_SYNC, {
        points: points,
      });

      this.isOnline = true;
    } catch (error) {
      console.error('[LocationService] Failed to sync offline data:', error);
      // Вернуть точки обратно в очередь
      const points = [...this.offlinePoints];
      this.offlinePoints.unshift(...points);
      this.isOnline = false;
    }
  }

  async getCurrentLocation(): Promise<LocationPoint> {
    return new Promise((resolve, reject) => {
      Geolocation.getCurrentPosition(
        position => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy_meters: position.coords.accuracy,
            altitude_meters: position.coords.altitude,
            speed_ms: position.coords.speed,
            heading_degrees: position.coords.heading,
            timestamp: new Date(position.timestamp).toISOString(),
          });
        },
        error => {
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 10000,
        },
      );
    });
  }
}

export const locationService = new LocationService();
