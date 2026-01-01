/**Экран карты.*/
import React, {useEffect, useState} from 'react';
import {View, StyleSheet, Text} from 'react-native';
import MapView, {Marker, Polygon} from 'react-native-maps';

import {useLocation} from '../../contexts/LocationContext';
import {apiService} from '../../services/api';
import {ENDPOINTS} from '../../config/api';

interface Geozone {
  id: number;
  name: string;
  center_latitude: string;
  center_longitude: string;
  geozone_type: string;
}

const MapScreen: React.FC = () => {
  const {currentLocation, getCurrentLocation} = useLocation();
  const [geozones, setGeozones] = useState<Geozone[]>([]);

  useEffect(() => {
    loadGeozones();
    getCurrentLocation();
  }, []);

  const loadGeozones = async (): Promise<void> => {
    try {
      const data = await apiService.get<Geozone[]>(ENDPOINTS.GEOZONE.LIST);
      setGeozones(data);
    } catch (error) {
      console.error('[MapScreen] Failed to load geozones:', error);
    }
  };

  if (!currentLocation) {
    return (
      <View style={styles.container}>
        <Text>Загрузка карты...</Text>
      </View>
    );
  }

  return (
    <MapView
      style={styles.map}
      initialRegion={{
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      }}>
      {currentLocation && (
        <Marker
          coordinate={{
            latitude: currentLocation.latitude,
            longitude: currentLocation.longitude,
          }}
          title="Вы здесь"
        />
      )}
      {geozones.map(geozone => (
        <Marker
          key={geozone.id}
          coordinate={{
            latitude: parseFloat(geozone.center_latitude),
            longitude: parseFloat(geozone.center_longitude),
          }}
          title={geozone.name}
        />
      ))}
    </MapView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  map: {
    flex: 1,
  },
});

export default MapScreen;
