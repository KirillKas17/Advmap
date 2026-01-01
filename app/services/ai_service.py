"""Сервис AI-помощника и планирования маршрутов."""
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.route import Route, RouteProgress, AIConversation, RouteStatus, RouteType
from app.models.location import LocationPoint, LocationSession
from app.models.geozone import Geozone

settings = get_settings()
logger = logging.getLogger(__name__)


class AIService:
    """Сервис для работы с AI-помощником."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db

    def generate_route(
        self,
        user_id: int,
        prompt: str,
        start_location: Optional[Dict] = None,
        company_id: Optional[int] = None,
    ) -> Route:
        """
        Сгенерировать маршрут с помощью AI.
        
        Args:
            user_id: ID пользователя
            prompt: Промпт для AI (например, "Хочу посетить музеи в центре Москвы")
            start_location: Начальная точка {"latitude": float, "longitude": float}
            company_id: ID компании
        """
        # В реальной реализации здесь был бы вызов AI API (OpenAI, Claude и т.д.)
        # Для MVP генерируем маршрут на основе геозон рядом с начальной точкой
        
        waypoints = []
        ai_response = f"Сгенерирован маршрут на основе вашего запроса: {prompt}"

        if start_location:
            # Найти геозоны рядом с начальной точкой
            from app.services.geozone import GeozoneService
            geozone_service = GeozoneService(self.db)
            nearby_geozones = geozone_service.find_geozones_by_point(
                latitude=start_location["latitude"],
                longitude=start_location["longitude"],
                company_id=company_id,
            )

            # Создать waypoints на основе найденных геозон
            waypoints = [
                {
                    "geozone_id": gz.id,
                    "latitude": float(gz.center_latitude),
                    "longitude": float(gz.center_longitude),
                    "name": gz.name,
                    "order": idx,
                }
                for idx, gz in enumerate(nearby_geozones[:10])  # Максимум 10 точек
            ]

            if waypoints:
                ai_response += f"\n\nНайдено {len(waypoints)} интересных мест рядом с вами."
        else:
            # Использовать последнее местоположение пользователя
            last_point = (
                self.db.query(LocationPoint)
                .join(LocationSession)
                .filter(LocationSession.user_id == user_id)
                .order_by(LocationPoint.timestamp.desc())
                .first()
            )
            if last_point:
                start_location = {
                    "latitude": last_point.latitude,
                    "longitude": last_point.longitude,
                }
                waypoints = [
                    {
                        "latitude": last_point.latitude,
                        "longitude": last_point.longitude,
                        "name": "Текущее местоположение",
                        "order": 0,
                    }
                ]

        route = Route(
            user_id=user_id,
            name=f"AI Маршрут: {prompt[:50]}",
            description=ai_response,
            route_type=RouteType.AI_GENERATED,
            status=RouteStatus.PLANNED,
            waypoints=waypoints,
            ai_prompt=prompt,
            ai_response=ai_response,
            company_id=company_id,
        )
        self.db.add(route)
        self.db.commit()
        self.db.refresh(route)
        logger.info(f"Сгенерирован AI маршрут: {route.id} для пользователя {user_id}")
        return route

    def get_contextual_recommendations(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        company_id: Optional[int] = None,
    ) -> List[Dict]:
        """Получить контекстные рекомендации на основе местоположения."""
        from app.services.geozone import GeozoneService
        from geopy.distance import distance

        geozone_service = GeozoneService(self.db)
        nearby_geozones = geozone_service.find_geozones_by_point(
            latitude=latitude,
            longitude=longitude,
            company_id=company_id,
        )

        # Фильтровать по радиусу и добавить расстояние
        recommendations = []
        for gz in nearby_geozones:
            dist = distance(
                (latitude, longitude),
                (float(gz.center_latitude), float(gz.center_longitude))
            ).km

            if dist <= radius_km:
                recommendations.append({
                    "geozone_id": gz.id,
                    "name": gz.name,
                    "description": gz.description,
                    "distance_km": round(dist, 2),
                    "type": gz.geozone_type,
                })

        # Сортировать по расстоянию
        recommendations.sort(key=lambda x: x["distance_km"])

        logger.debug(f"Получено {len(recommendations)} рекомендаций для пользователя {user_id}")
        return recommendations[:10]  # Вернуть топ-10

    def create_conversation(
        self,
        user_id: int,
        conversation_type: str,
        initial_message: str,
        context_data: Optional[Dict] = None,
        company_id: Optional[int] = None,
    ) -> AIConversation:
        """Создать разговор с AI."""
        messages = [
            {
                "role": "user",
                "content": initial_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]

        # Генерировать ответ AI (в реальной реализации - вызов AI API)
        ai_response = self._generate_ai_response(initial_message, conversation_type, context_data)
        messages.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        conversation = AIConversation(
            user_id=user_id,
            conversation_type=conversation_type,
            messages=messages,
            context_data=context_data or {},
            company_id=company_id,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        logger.info(f"Создан разговор с AI: {conversation.id} для пользователя {user_id}")
        return conversation

    def add_message_to_conversation(
        self,
        conversation_id: int,
        message: str,
        company_id: Optional[int] = None,
    ) -> AIConversation:
        """Добавить сообщение в разговор."""
        conversation = (
            self.db.query(AIConversation)
            .filter(AIConversation.id == conversation_id)
        )
        if company_id is not None:
            conversation = conversation.filter(AIConversation.company_id == company_id)
        conversation = conversation.first()

        if not conversation:
            raise ValueError("Разговор не найден")

        # Добавить сообщение пользователя
        messages = conversation.messages
        messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Генерировать ответ AI
        ai_response = self._generate_ai_response(
            message,
            conversation.conversation_type,
            conversation.context_data
        )
        messages.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        conversation.messages = messages
        conversation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def _generate_ai_response(
        self,
        message: str,
        conversation_type: str,
        context_data: Optional[Dict] = None,
    ) -> str:
        """Сгенерировать ответ AI (заглушка для MVP)."""
        # В реальной реализации здесь был бы вызов AI API
        # Для MVP возвращаем простые ответы
        
        if conversation_type == "route_planning":
            return f"Я помогу вам спланировать маршрут. На основе вашего запроса '{message}', я могу предложить несколько интересных мест для посещения."
        elif conversation_type == "recommendation":
            return f"Учитывая ваш запрос '{message}', рекомендую посетить места, которые соответствуют вашим интересам."
        else:
            return f"Я готов помочь вам с '{message}'. Что именно вас интересует?"
