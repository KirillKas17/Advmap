"""Модели базы данных."""
from app.models.achievement import Achievement, UserAchievement
from app.models.geozone import Geozone, GeozoneVisit, AreaDiscovery
from app.models.location import LocationPoint, LocationSession
from app.models.user import User
from app.models.user_home_work import UserHomeWork
from app.models.artifact import Artifact, UserArtifact, ArtifactCraftingRequirement
from app.models.cosmetic import Cosmetic, UserCosmetic, CosmeticCraftingRequirement, UserAvatar
from app.models.marketplace import MarketplaceListing, Transaction, UserCurrency, CurrencyTransaction
from app.models.event import Event, Quest, UserQuest, UserEvent
from app.models.guild import Guild, GuildMember, GuildAchievement
from app.models.verification import VerificationRequest, UserStatusHistory
from app.models.creator import Creator, CreatorPayment, QuestModeration
from app.models.route import Route, RouteProgress, AIConversation
from app.models.memory import Memory, MemoryTimeline
from app.models.portal import Portal, PortalInteraction
from app.models.analytics import BusinessClient, AnalyticsDashboard, AnalyticsExport

__all__ = [
    "User",
    "Achievement",
    "UserAchievement",
    "Geozone",
    "GeozoneVisit",
    "AreaDiscovery",
    "LocationPoint",
    "LocationSession",
    "UserHomeWork",
    "Artifact",
    "UserArtifact",
    "ArtifactCraftingRequirement",
    "Cosmetic",
    "UserCosmetic",
    "CosmeticCraftingRequirement",
    "UserAvatar",
    "MarketplaceListing",
    "Transaction",
    "UserCurrency",
    "CurrencyTransaction",
    "Event",
    "Quest",
    "UserQuest",
    "UserEvent",
    "Guild",
    "GuildMember",
    "GuildAchievement",
    "VerificationRequest",
    "UserStatusHistory",
    "Creator",
    "CreatorPayment",
    "QuestModeration",
    "Route",
    "RouteProgress",
    "AIConversation",
    "Memory",
    "MemoryTimeline",
    "Portal",
    "PortalInteraction",
    "BusinessClient",
    "AnalyticsDashboard",
    "AnalyticsExport",
]
