/**Главный навигатор.*/
import React from 'react';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';

import MapScreen from '../screens/main/MapScreen';
import AchievementsScreen from '../screens/main/AchievementsScreen';
import ProfileScreen from '../screens/main/ProfileScreen';

const Tab = createBottomTabNavigator();

const MainNavigator: React.FC = () => {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Map" component={MapScreen} options={{title: 'Карта'}} />
      <Tab.Screen
        name="Achievements"
        component={AchievementsScreen}
        options={{title: 'Достижения'}}
      />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{title: 'Профиль'}} />
    </Tab.Navigator>
  );
};

export default MainNavigator;
