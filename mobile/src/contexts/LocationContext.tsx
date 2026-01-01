/**Контекст геолокации.*/
import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';

import {locationService} from '../services/locationService';
import {useAuth} from './AuthContext';

interface LocationPoint {
  latitude: number;
  longitude: number;
  accuracy_meters?: number;
  timestamp: string;
}

interface LocationContextType {
  currentLocation: LocationPoint | null;
  isTracking: boolean;
  startTracking: () => Promise<void>;
  stopTracking: () => Promise<void>;
  getCurrentLocation: () => Promise<LocationPoint>;
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export const LocationProvider: React.FC<{children: ReactNode}> = ({children}) => {
  const {isAuthenticated} = useAuth();
  const [currentLocation, setCurrentLocation] = useState<LocationPoint | null>(null);
  const [isTracking, setIsTracking] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      // Автоматически начать отслеживание при входе
      startTracking();
    } else {
      stopTracking();
    }

    return () => {
      stopTracking();
    };
  }, [isAuthenticated]);

  const startTracking = async (): Promise<void> => {
    try {
      await locationService.startTracking();
      setIsTracking(true);
    } catch (error) {
      console.error('[LocationContext] Failed to start tracking:', error);
    }
  };

  const stopTracking = async (): Promise<void> => {
    try {
      await locationService.stopTracking();
      setIsTracking(false);
    } catch (error) {
      console.error('[LocationContext] Failed to stop tracking:', error);
    }
  };

  const getCurrentLocation = async (): Promise<LocationPoint> => {
    const location = await locationService.getCurrentLocation();
    setCurrentLocation(location);
    return location;
  };

  return (
    <LocationContext.Provider
      value={{
        currentLocation,
        isTracking,
        startTracking,
        stopTracking,
        getCurrentLocation,
      }}>
      {children}
    </LocationContext.Provider>
  );
};

export const useLocation = (): LocationContextType => {
  const context = useContext(LocationContext);
  if (context === undefined) {
    throw new Error('useLocation must be used within a LocationProvider');
  }
  return context;
};
