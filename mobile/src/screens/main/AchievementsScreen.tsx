/**Экран достижений.*/
import React, {useEffect, useState} from 'react';
import {View, Text, FlatList, StyleSheet} from 'react-native';

import {apiService} from '../../services/api';
import {ENDPOINTS} from '../../config/api';

interface UserAchievement {
  id: number;
  achievement_id: number;
  unlocked_at: string;
  progress_value: number;
  achievement?: {
    id: number;
    name: string;
    description?: string;
    icon_url?: string;
  };
}

const AchievementsScreen: React.FC = () => {
  const [achievements, setAchievements] = useState<UserAchievement[]>([]);

  useEffect(() => {
    loadAchievements();
  }, []);

  const loadAchievements = async (): Promise<void> => {
    try {
      const data = await apiService.get<UserAchievement[]>(ENDPOINTS.ACHIEVEMENT.MY);
      setAchievements(data);
    } catch (error) {
      console.error('[AchievementsScreen] Failed to load achievements:', error);
    }
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={achievements}
        keyExtractor={item => item.id.toString()}
        renderItem={({item}) => (
          <View style={styles.achievementItem}>
            <Text style={styles.achievementName}>
              {item.achievement?.name || `Достижение #${item.achievement_id}`}
            </Text>
            {item.achievement?.description && (
              <Text style={styles.achievementDescription}>{item.achievement.description}</Text>
            )}
            <Text style={styles.unlockedDate}>
              Разблокировано: {new Date(item.unlocked_at).toLocaleDateString()}
            </Text>
          </View>
        )}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>У вас пока нет достижений</Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  achievementItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  achievementName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  achievementDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  unlockedDate: {
    fontSize: 12,
    color: '#999',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
});

export default AchievementsScreen;
