"""Add v2, v3, v4 features

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Версия 2.0: Артефакты
    op.create_table(
        'artifacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('rarity', sa.String(length=50), nullable=False),
        sa.Column('artifact_type', sa.String(length=50), nullable=False),
        sa.Column('geozone_id', sa.Integer(), nullable=True),
        sa.Column('region_name', sa.String(length=255), nullable=True),
        sa.Column('drop_chance', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_tradeable', sa.Boolean(), nullable=False),
        sa.Column('is_craftable', sa.Boolean(), nullable=False),
        sa.Column('base_value', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['geozone_id'], ['geozones.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artifacts_id'), 'artifacts', ['id'], unique=False)
    op.create_index(op.f('ix_artifacts_name'), 'artifacts', ['name'], unique=False)
    op.create_index(op.f('ix_artifacts_rarity'), 'artifacts', ['rarity'], unique=False)
    op.create_index(op.f('ix_artifacts_artifact_type'), 'artifacts', ['artifact_type'], unique=False)
    op.create_index(op.f('ix_artifacts_geozone_id'), 'artifacts', ['geozone_id'], unique=False)
    op.create_index(op.f('ix_artifacts_region_name'), 'artifacts', ['region_name'], unique=False)
    op.create_index(op.f('ix_artifacts_company_id'), 'artifacts', ['company_id'], unique=False)

    op.create_table(
        'user_artifacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('artifact_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('obtained_at', sa.DateTime(), nullable=False),
        sa.Column('obtained_from', sa.String(length=100), nullable=True),
        sa.Column('obtained_from_id', sa.Integer(), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_artifacts_id'), 'user_artifacts', ['id'], unique=False)
    op.create_index(op.f('ix_user_artifacts_user_id'), 'user_artifacts', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_artifacts_artifact_id'), 'user_artifacts', ['artifact_id'], unique=False)
    op.create_index(op.f('ix_user_artifacts_obtained_at'), 'user_artifacts', ['obtained_at'], unique=False)
    op.create_index(op.f('ix_user_artifacts_company_id'), 'user_artifacts', ['company_id'], unique=False)

    op.create_table(
        'artifact_crafting_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('artifact_id', sa.Integer(), nullable=False),
        sa.Column('required_artifact_id', sa.Integer(), nullable=False),
        sa.Column('required_quantity', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['required_artifact_id'], ['artifacts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artifact_crafting_requirements_id'), 'artifact_crafting_requirements', ['id'], unique=False)
    op.create_index(op.f('ix_artifact_crafting_requirements_artifact_id'), 'artifact_crafting_requirements', ['artifact_id'], unique=False)
    op.create_index(op.f('ix_artifact_crafting_requirements_required_artifact_id'), 'artifact_crafting_requirements', ['required_artifact_id'], unique=False)

    # Версия 2.0: Косметика
    op.create_table(
        'cosmetics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('preview_url', sa.String(length=500), nullable=True),
        sa.Column('cosmetic_type', sa.String(length=50), nullable=False),
        sa.Column('rarity', sa.String(length=50), nullable=False),
        sa.Column('slot', sa.String(length=50), nullable=True),
        sa.Column('customization_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_tradeable', sa.Boolean(), nullable=False),
        sa.Column('is_craftable', sa.Boolean(), nullable=False),
        sa.Column('base_value', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cosmetics_id'), 'cosmetics', ['id'], unique=False)
    op.create_index(op.f('ix_cosmetics_name'), 'cosmetics', ['name'], unique=False)
    op.create_index(op.f('ix_cosmetics_cosmetic_type'), 'cosmetics', ['cosmetic_type'], unique=False)
    op.create_index(op.f('ix_cosmetics_rarity'), 'cosmetics', ['rarity'], unique=False)
    op.create_index(op.f('ix_cosmetics_company_id'), 'cosmetics', ['company_id'], unique=False)

    op.create_table(
        'user_cosmetics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('cosmetic_id', sa.Integer(), nullable=False),
        sa.Column('is_equipped', sa.Boolean(), nullable=False),
        sa.Column('obtained_at', sa.DateTime(), nullable=False),
        sa.Column('obtained_from', sa.String(length=100), nullable=True),
        sa.Column('obtained_from_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cosmetic_id'], ['cosmetics.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_cosmetics_id'), 'user_cosmetics', ['id'], unique=False)
    op.create_index(op.f('ix_user_cosmetics_user_id'), 'user_cosmetics', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_cosmetics_cosmetic_id'), 'user_cosmetics', ['cosmetic_id'], unique=False)
    op.create_index(op.f('ix_user_cosmetics_obtained_at'), 'user_cosmetics', ['obtained_at'], unique=False)
    op.create_index(op.f('ix_user_cosmetics_company_id'), 'user_cosmetics', ['company_id'], unique=False)

    op.create_table(
        'cosmetic_crafting_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cosmetic_id', sa.Integer(), nullable=False),
        sa.Column('required_artifact_id', sa.Integer(), nullable=True),
        sa.Column('required_cosmetic_id', sa.Integer(), nullable=True),
        sa.Column('required_quantity', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cosmetic_id'], ['cosmetics.id'], ),
        sa.ForeignKeyConstraint(['required_artifact_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['required_cosmetic_id'], ['cosmetics.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cosmetic_crafting_requirements_id'), 'cosmetic_crafting_requirements', ['id'], unique=False)
    op.create_index(op.f('ix_cosmetic_crafting_requirements_cosmetic_id'), 'cosmetic_crafting_requirements', ['cosmetic_id'], unique=False)

    op.create_table(
        'user_avatars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('avatar_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_avatars_id'), 'user_avatars', ['id'], unique=False)
    op.create_index(op.f('ix_user_avatars_user_id'), 'user_avatars', ['user_id'], unique=True)

    # Версия 2.0: Торговая площадка
    op.create_table(
        'user_currency',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('coins', sa.Integer(), nullable=False),
        sa.Column('gems', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_currency_id'), 'user_currency', ['id'], unique=False)
    op.create_index(op.f('ix_user_currency_user_id'), 'user_currency', ['user_id'], unique=True)

    op.create_table(
        'currency_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_currency_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency_type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('related_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_currency_id'], ['user_currency.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_currency_transactions_id'), 'currency_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_currency_transactions_user_currency_id'), 'currency_transactions', ['user_currency_id'], unique=False)
    op.create_index(op.f('ix_currency_transactions_transaction_type'), 'currency_transactions', ['transaction_type'], unique=False)

    op.create_table(
        'marketplace_listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('listing_type', sa.Enum('ARTIFACT', 'COSMETIC', name='listingtype'), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'SOLD', 'CANCELLED', 'EXPIRED', name='listingstatus'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketplace_listings_id'), 'marketplace_listings', ['id'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_seller_id'), 'marketplace_listings', ['seller_id'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_listing_type'), 'marketplace_listings', ['listing_type'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_item_id'), 'marketplace_listings', ['item_id'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_status'), 'marketplace_listings', ['status'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_company_id'), 'marketplace_listings', ['company_id'], unique=False)

    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('listing_type', sa.Enum('ARTIFACT', 'COSMETIC', name='listingtype'), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'CANCELLED', 'FAILED', name='transactionstatus'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['listing_id'], ['marketplace_listings.id'], ),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_listing_id'), 'transactions', ['listing_id'], unique=False)
    op.create_index(op.f('ix_transactions_buyer_id'), 'transactions', ['buyer_id'], unique=False)
    op.create_index(op.f('ix_transactions_seller_id'), 'transactions', ['seller_id'], unique=False)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)
    op.create_index(op.f('ix_transactions_company_id'), 'transactions', ['company_id'], unique=False)

    # Версия 2.0: События и квесты
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('event_type', sa.Enum('SEASONAL', 'LIMITED', 'WEEKLY', 'DAILY', 'SPECIAL', name='eventtype'), nullable=False),
        sa.Column('status', sa.Enum('UPCOMING', 'ACTIVE', 'ENDED', 'CANCELLED', name='eventstatus'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('reward_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_name'), 'events', ['name'], unique=False)
    op.create_index(op.f('ix_events_event_type'), 'events', ['event_type'], unique=False)
    op.create_index(op.f('ix_events_status'), 'events', ['status'], unique=False)
    op.create_index(op.f('ix_events_start_date'), 'events', ['start_date'], unique=False)
    op.create_index(op.f('ix_events_end_date'), 'events', ['end_date'], unique=False)
    op.create_index(op.f('ix_events_company_id'), 'events', ['company_id'], unique=False)

    op.create_table(
        'quests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('quest_type', sa.Enum('VISIT_LOCATIONS', 'COLLECT_ARTIFACTS', 'TRAVEL_DISTANCE', 'COMPLETE_ACHIEVEMENTS', 'CUSTOM', name='questtype'), nullable=False),
        sa.Column('requirements', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('rewards', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_repeatable', sa.Boolean(), nullable=False),
        sa.Column('max_completions', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_premium', sa.Boolean(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quests_id'), 'quests', ['id'], unique=False)
    op.create_index(op.f('ix_quests_name'), 'quests', ['name'], unique=False)
    op.create_index(op.f('ix_quests_quest_type'), 'quests', ['quest_type'], unique=False)
    op.create_index(op.f('ix_quests_event_id'), 'quests', ['event_id'], unique=False)
    op.create_index(op.f('ix_quests_company_id'), 'quests', ['company_id'], unique=False)

    op.create_table(
        'user_quests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('quest_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('AVAILABLE', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'EXPIRED', name='queststatus'), nullable=False),
        sa.Column('progress', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('completion_count', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_quests_id'), 'user_quests', ['id'], unique=False)
    op.create_index(op.f('ix_user_quests_user_id'), 'user_quests', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_quests_quest_id'), 'user_quests', ['quest_id'], unique=False)
    op.create_index(op.f('ix_user_quests_status'), 'user_quests', ['status'], unique=False)
    op.create_index(op.f('ix_user_quests_company_id'), 'user_quests', ['company_id'], unique=False)

    op.create_table(
        'user_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('participation_score', sa.Integer(), nullable=False),
        sa.Column('rewards_claimed', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_events_id'), 'user_events', ['id'], unique=False)
    op.create_index(op.f('ix_user_events_user_id'), 'user_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_events_event_id'), 'user_events', ['event_id'], unique=False)
    op.create_index(op.f('ix_user_events_company_id'), 'user_events', ['company_id'], unique=False)

    # Версия 3.0: Гильдии
    op.create_table(
        'guilds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tag', sa.String(length=10), nullable=True),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DISBANDED', name='guildstatus'), nullable=False),
        sa.Column('max_members', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('experience', sa.Integer(), nullable=False),
        sa.Column('total_achievements', sa.Integer(), nullable=False),
        sa.Column('total_distance', sa.Float(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('tag')
    )
    op.create_index(op.f('ix_guilds_id'), 'guilds', ['id'], unique=False)
    op.create_index(op.f('ix_guilds_name'), 'guilds', ['name'], unique=True)
    op.create_index(op.f('ix_guilds_status'), 'guilds', ['status'], unique=False)
    op.create_index(op.f('ix_guilds_company_id'), 'guilds', ['company_id'], unique=False)

    op.create_table(
        'guild_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('MEMBER', 'OFFICER', 'LEADER', name='guildrole'), nullable=False),
        sa.Column('contribution_score', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guild_members_id'), 'guild_members', ['id'], unique=False)
    op.create_index(op.f('ix_guild_members_guild_id'), 'guild_members', ['guild_id'], unique=False)
    op.create_index(op.f('ix_guild_members_user_id'), 'guild_members', ['user_id'], unique=False)
    op.create_index(op.f('ix_guild_members_role'), 'guild_members', ['role'], unique=False)
    op.create_index(op.f('ix_guild_members_company_id'), 'guild_members', ['company_id'], unique=False)

    op.create_table(
        'guild_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=False),
        sa.Column('unlocked_by_user_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['unlocked_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guild_achievements_id'), 'guild_achievements', ['id'], unique=False)
    op.create_index(op.f('ix_guild_achievements_guild_id'), 'guild_achievements', ['guild_id'], unique=False)
    op.create_index(op.f('ix_guild_achievements_achievement_id'), 'guild_achievements', ['achievement_id'], unique=False)
    op.create_index(op.f('ix_guild_achievements_unlocked_at'), 'guild_achievements', ['unlocked_at'], unique=False)

    # Версия 3.0: Верификация
    op.create_table(
        'verification_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'REVOKED', name='verificationstatus'), nullable=False),
        sa.Column('requested_status', sa.Enum('NEWBIE', 'TRAVELER', 'EXPLORER', 'VERIFIED_TRAVELER', 'MASTER_EXPLORER', 'LEGEND', name='userstatus'), nullable=False),
        sa.Column('evidence_data', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_requests_id'), 'verification_requests', ['id'], unique=False)
    op.create_index(op.f('ix_verification_requests_user_id'), 'verification_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_verification_requests_status'), 'verification_requests', ['status'], unique=False)
    op.create_index(op.f('ix_verification_requests_company_id'), 'verification_requests', ['company_id'], unique=False)

    op.create_table(
        'user_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('old_status', sa.Enum('NEWBIE', 'TRAVELER', 'EXPLORER', 'VERIFIED_TRAVELER', 'MASTER_EXPLORER', 'LEGEND', name='userstatus'), nullable=True),
        sa.Column('new_status', sa.Enum('NEWBIE', 'TRAVELER', 'EXPLORER', 'VERIFIED_TRAVELER', 'MASTER_EXPLORER', 'LEGEND', name='userstatus'), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_status_history_id'), 'user_status_history', ['id'], unique=False)
    op.create_index(op.f('ix_user_status_history_user_id'), 'user_status_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_status_history_company_id'), 'user_status_history', ['company_id'], unique=False)

    # Версия 3.0: Платформа для создателей
    op.create_table(
        'creators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED', name='creatorstatus'), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('total_quests_created', sa.Integer(), nullable=False),
        sa.Column('total_quests_sold', sa.Integer(), nullable=False),
        sa.Column('total_revenue', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('total_ratings', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_creators_id'), 'creators', ['id'], unique=False)
    op.create_index(op.f('ix_creators_user_id'), 'creators', ['user_id'], unique=True)
    op.create_index(op.f('ix_creators_status'), 'creators', ['status'], unique=False)
    op.create_index(op.f('ix_creators_company_id'), 'creators', ['company_id'], unique=False)

    op.create_table(
        'creator_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('quest_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('platform_fee', sa.Integer(), nullable=False),
        sa.Column('creator_earnings', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_creator_payments_id'), 'creator_payments', ['id'], unique=False)
    op.create_index(op.f('ix_creator_payments_creator_id'), 'creator_payments', ['creator_id'], unique=False)
    op.create_index(op.f('ix_creator_payments_quest_id'), 'creator_payments', ['quest_id'], unique=False)
    op.create_index(op.f('ix_creator_payments_buyer_id'), 'creator_payments', ['buyer_id'], unique=False)
    op.create_index(op.f('ix_creator_payments_status'), 'creator_payments', ['status'], unique=False)

    op.create_table(
        'quest_moderations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quest_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'NEEDS_REVISION', name='questmoderationstatus'), nullable=False),
        sa.Column('moderation_notes', sa.Text(), nullable=True),
        sa.Column('moderated_by', sa.Integer(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['moderated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quest_id')
    )
    op.create_index(op.f('ix_quest_moderations_id'), 'quest_moderations', ['id'], unique=False)
    op.create_index(op.f('ix_quest_moderations_quest_id'), 'quest_moderations', ['quest_id'], unique=True)
    op.create_index(op.f('ix_quest_moderations_status'), 'quest_moderations', ['status'], unique=False)

    # Версия 4.0: AI и маршруты
    op.create_table(
        'routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('route_type', sa.Enum('AI_GENERATED', 'MANUAL', 'TEMPLATE', name='routetype'), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='routestatus'), nullable=False),
        sa.Column('waypoints', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('estimated_duration_hours', sa.Float(), nullable=True),
        sa.Column('estimated_distance_km', sa.Float(), nullable=True),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_template', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_routes_id'), 'routes', ['id'], unique=False)
    op.create_index(op.f('ix_routes_user_id'), 'routes', ['user_id'], unique=False)
    op.create_index(op.f('ix_routes_route_type'), 'routes', ['route_type'], unique=False)
    op.create_index(op.f('ix_routes_status'), 'routes', ['status'], unique=False)
    op.create_index(op.f('ix_routes_company_id'), 'routes', ['company_id'], unique=False)

    op.create_table(
        'route_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_waypoint_index', sa.Integer(), nullable=False),
        sa.Column('visited_waypoints', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('completion_percentage', sa.Float(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_route_progress_id'), 'route_progress', ['id'], unique=False)
    op.create_index(op.f('ix_route_progress_route_id'), 'route_progress', ['route_id'], unique=False)
    op.create_index(op.f('ix_route_progress_user_id'), 'route_progress', ['user_id'], unique=False)

    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversation_type', sa.String(length=50), nullable=False),
        sa.Column('messages', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_conversations_id'), 'ai_conversations', ['id'], unique=False)
    op.create_index(op.f('ix_ai_conversations_user_id'), 'ai_conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_ai_conversations_conversation_type'), 'ai_conversations', ['conversation_type'], unique=False)

    # Версия 4.0: Метавселенная воспоминаний
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('memory_type', sa.String(length=50), nullable=False),
        sa.Column('location_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('media_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('emotion_score', sa.Float(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=False),
        sa.Column('related_geozone_id', sa.Integer(), nullable=True),
        sa.Column('related_achievement_id', sa.Integer(), nullable=True),
        sa.Column('related_event_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['related_achievement_id'], ['achievements.id'], ),
        sa.ForeignKeyConstraint(['related_event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['related_geozone_id'], ['geozones.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memories_id'), 'memories', ['id'], unique=False)
    op.create_index(op.f('ix_memories_user_id'), 'memories', ['user_id'], unique=False)
    op.create_index(op.f('ix_memories_memory_type'), 'memories', ['memory_type'], unique=False)
    op.create_index(op.f('ix_memories_company_id'), 'memories', ['company_id'], unique=False)

    op.create_table(
        'memory_timeline',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('memory_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=True),
        sa.Column('position_y', sa.Float(), nullable=True),
        sa.Column('position_z', sa.Float(), nullable=True),
        sa.Column('rotation', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('scale', sa.Float(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_timeline_id'), 'memory_timeline', ['id'], unique=False)
    op.create_index(op.f('ix_memory_timeline_memory_id'), 'memory_timeline', ['memory_id'], unique=False)
    op.create_index(op.f('ix_memory_timeline_user_id'), 'memory_timeline', ['user_id'], unique=False)

    # Версия 4.0: Порталы
    op.create_table(
        'portals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('portal_type', sa.Enum('TOTEM', 'PORTAL', 'BEACON', name='portaltype'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DESTROYED', name='portalstatus'), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('point', Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('installed_artifact_id', sa.Integer(), nullable=True),
        sa.Column('installed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('installed_at', sa.DateTime(), nullable=True),
        sa.Column('interaction_count', sa.Integer(), nullable=False),
        sa.Column('last_interaction_at', sa.DateTime(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['installed_artifact_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['installed_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portals_id'), 'portals', ['id'], unique=False)
    op.create_index(op.f('ix_portals_portal_type'), 'portals', ['portal_type'], unique=False)
    op.create_index(op.f('ix_portals_status'), 'portals', ['status'], unique=False)
    op.create_index('idx_portal_point', 'portals', ['point'], unique=False, postgresql_using='gist')

    op.create_table(
        'portal_interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portal_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('interaction_type', sa.String(length=50), nullable=False),
        sa.Column('artifact_left_id', sa.Integer(), nullable=True),
        sa.Column('artifact_taken_id', sa.Integer(), nullable=True),
        sa.Column('reward_received', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['artifact_left_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['artifact_taken_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['portal_id'], ['portals.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portal_interactions_id'), 'portal_interactions', ['id'], unique=False)
    op.create_index(op.f('ix_portal_interactions_portal_id'), 'portal_interactions', ['portal_id'], unique=False)
    op.create_index(op.f('ix_portal_interactions_user_id'), 'portal_interactions', ['user_id'], unique=False)

    # Версия 5.0: B2B аналитика
    op.create_table(
        'business_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('subscription_status', sa.Enum('ACTIVE', 'EXPIRED', 'CANCELLED', 'SUSPENDED', name='subscriptionstatus'), nullable=False),
        sa.Column('subscription_tier', sa.String(length=50), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('max_api_calls_per_day', sa.Integer(), nullable=False),
        sa.Column('current_api_calls_today', sa.Integer(), nullable=False),
        sa.Column('last_api_call_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key')
    )
    op.create_index(op.f('ix_business_clients_id'), 'business_clients', ['id'], unique=False)
    op.create_index(op.f('ix_business_clients_company_name'), 'business_clients', ['company_name'], unique=False)
    op.create_index(op.f('ix_business_clients_subscription_status'), 'business_clients', ['subscription_status'], unique=False)
    op.create_index(op.f('ix_business_clients_api_key'), 'business_clients', ['api_key'], unique=True)
    op.create_index(op.f('ix_business_clients_company_id'), 'business_clients', ['company_id'], unique=False)

    op.create_table(
        'analytics_dashboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('dashboard_type', sa.Enum('TOURISM', 'RETAIL', 'MARKETING', 'CUSTOM', name='dashboardtype'), nullable=False),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['business_clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_dashboards_id'), 'analytics_dashboards', ['id'], unique=False)
    op.create_index(op.f('ix_analytics_dashboards_client_id'), 'analytics_dashboards', ['client_id'], unique=False)
    op.create_index(op.f('ix_analytics_dashboards_name'), 'analytics_dashboards', ['name'], unique=False)
    op.create_index(op.f('ix_analytics_dashboards_dashboard_type'), 'analytics_dashboards', ['dashboard_type'], unique=False)

    op.create_table(
        'analytics_exports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('export_type', sa.String(length=50), nullable=False),
        sa.Column('data_range_start', sa.DateTime(), nullable=False),
        sa.Column('data_range_end', sa.DateTime(), nullable=False),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['business_clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_exports_id'), 'analytics_exports', ['id'], unique=False)
    op.create_index(op.f('ix_analytics_exports_client_id'), 'analytics_exports', ['client_id'], unique=False)
    op.create_index(op.f('ix_analytics_exports_status'), 'analytics_exports', ['status'], unique=False)


def downgrade() -> None:
    # Удаление в обратном порядке
    op.drop_index(op.f('ix_analytics_exports_status'), table_name='analytics_exports')
    op.drop_index(op.f('ix_analytics_exports_client_id'), table_name='analytics_exports')
    op.drop_index(op.f('ix_analytics_exports_id'), table_name='analytics_exports')
    op.drop_table('analytics_exports')
    op.drop_index(op.f('ix_analytics_dashboards_dashboard_type'), table_name='analytics_dashboards')
    op.drop_index(op.f('ix_analytics_dashboards_name'), table_name='analytics_dashboards')
    op.drop_index(op.f('ix_analytics_dashboards_client_id'), table_name='analytics_dashboards')
    op.drop_index(op.f('ix_analytics_dashboards_id'), table_name='analytics_dashboards')
    op.drop_table('analytics_dashboards')
    op.drop_index(op.f('ix_business_clients_company_id'), table_name='business_clients')
    op.drop_index(op.f('ix_business_clients_api_key'), table_name='business_clients')
    op.drop_index(op.f('ix_business_clients_subscription_status'), table_name='business_clients')
    op.drop_index(op.f('ix_business_clients_company_name'), table_name='business_clients')
    op.drop_index(op.f('ix_business_clients_id'), table_name='business_clients')
    op.drop_table('business_clients')
    op.drop_index(op.f('ix_portal_interactions_user_id'), table_name='portal_interactions')
    op.drop_index(op.f('ix_portal_interactions_portal_id'), table_name='portal_interactions')
    op.drop_index(op.f('ix_portal_interactions_id'), table_name='portal_interactions')
    op.drop_table('portal_interactions')
    op.drop_index('idx_portal_point', table_name='portals')
    op.drop_index(op.f('ix_portals_status'), table_name='portals')
    op.drop_index(op.f('ix_portals_portal_type'), table_name='portals')
    op.drop_index(op.f('ix_portals_id'), table_name='portals')
    op.drop_table('portals')
    op.drop_index(op.f('ix_memory_timeline_user_id'), table_name='memory_timeline')
    op.drop_index(op.f('ix_memory_timeline_memory_id'), table_name='memory_timeline')
    op.drop_index(op.f('ix_memory_timeline_id'), table_name='memory_timeline')
    op.drop_table('memory_timeline')
    op.drop_index(op.f('ix_memories_company_id'), table_name='memories')
    op.drop_index(op.f('ix_memories_memory_type'), table_name='memories')
    op.drop_index(op.f('ix_memories_user_id'), table_name='memories')
    op.drop_index(op.f('ix_memories_id'), table_name='memories')
    op.drop_table('memories')
    op.drop_index(op.f('ix_ai_conversations_conversation_type'), table_name='ai_conversations')
    op.drop_index(op.f('ix_ai_conversations_user_id'), table_name='ai_conversations')
    op.drop_index(op.f('ix_ai_conversations_id'), table_name='ai_conversations')
    op.drop_table('ai_conversations')
    op.drop_index(op.f('ix_route_progress_user_id'), table_name='route_progress')
    op.drop_index(op.f('ix_route_progress_route_id'), table_name='route_progress')
    op.drop_index(op.f('ix_route_progress_id'), table_name='route_progress')
    op.drop_table('route_progress')
    op.drop_index(op.f('ix_routes_company_id'), table_name='routes')
    op.drop_index(op.f('ix_routes_status'), table_name='routes')
    op.drop_index(op.f('ix_routes_route_type'), table_name='routes')
    op.drop_index(op.f('ix_routes_user_id'), table_name='routes')
    op.drop_index(op.f('ix_routes_id'), table_name='routes')
    op.drop_table('routes')
    op.drop_index(op.f('ix_quest_moderations_status'), table_name='quest_moderations')
    op.drop_index(op.f('ix_quest_moderations_quest_id'), table_name='quest_moderations')
    op.drop_index(op.f('ix_quest_moderations_id'), table_name='quest_moderations')
    op.drop_table('quest_moderations')
    op.drop_index(op.f('ix_creator_payments_status'), table_name='creator_payments')
    op.drop_index(op.f('ix_creator_payments_buyer_id'), table_name='creator_payments')
    op.drop_index(op.f('ix_creator_payments_quest_id'), table_name='creator_payments')
    op.drop_index(op.f('ix_creator_payments_creator_id'), table_name='creator_payments')
    op.drop_index(op.f('ix_creator_payments_id'), table_name='creator_payments')
    op.drop_table('creator_payments')
    op.drop_index(op.f('ix_creators_company_id'), table_name='creators')
    op.drop_index(op.f('ix_creators_status'), table_name='creators')
    op.drop_index(op.f('ix_creators_user_id'), table_name='creators')
    op.drop_index(op.f('ix_creators_id'), table_name='creators')
    op.drop_table('creators')
    op.drop_index(op.f('ix_user_status_history_company_id'), table_name='user_status_history')
    op.drop_index(op.f('ix_user_status_history_user_id'), table_name='user_status_history')
    op.drop_index(op.f('ix_user_status_history_id'), table_name='user_status_history')
    op.drop_table('user_status_history')
    op.drop_index(op.f('ix_verification_requests_company_id'), table_name='verification_requests')
    op.drop_index(op.f('ix_verification_requests_status'), table_name='verification_requests')
    op.drop_index(op.f('ix_verification_requests_user_id'), table_name='verification_requests')
    op.drop_index(op.f('ix_verification_requests_id'), table_name='verification_requests')
    op.drop_table('verification_requests')
    op.drop_index(op.f('ix_guild_achievements_unlocked_at'), table_name='guild_achievements')
    op.drop_index(op.f('ix_guild_achievements_achievement_id'), table_name='guild_achievements')
    op.drop_index(op.f('ix_guild_achievements_guild_id'), table_name='guild_achievements')
    op.drop_index(op.f('ix_guild_achievements_id'), table_name='guild_achievements')
    op.drop_table('guild_achievements')
    op.drop_index(op.f('ix_guild_members_company_id'), table_name='guild_members')
    op.drop_index(op.f('ix_guild_members_role'), table_name='guild_members')
    op.drop_index(op.f('ix_guild_members_user_id'), table_name='guild_members')
    op.drop_index(op.f('ix_guild_members_guild_id'), table_name='guild_members')
    op.drop_index(op.f('ix_guild_members_id'), table_name='guild_members')
    op.drop_table('guild_members')
    op.drop_index(op.f('ix_guilds_company_id'), table_name='guilds')
    op.drop_index(op.f('ix_guilds_status'), table_name='guilds')
    op.drop_index(op.f('ix_guilds_name'), table_name='guilds')
    op.drop_index(op.f('ix_guilds_id'), table_name='guilds')
    op.drop_table('guilds')
    op.drop_index(op.f('ix_user_events_company_id'), table_name='user_events')
    op.drop_index(op.f('ix_user_events_event_id'), table_name='user_events')
    op.drop_index(op.f('ix_user_events_user_id'), table_name='user_events')
    op.drop_index(op.f('ix_user_events_id'), table_name='user_events')
    op.drop_table('user_events')
    op.drop_index(op.f('ix_user_quests_company_id'), table_name='user_quests')
    op.drop_index(op.f('ix_user_quests_status'), table_name='user_quests')
    op.drop_index(op.f('ix_user_quests_quest_id'), table_name='user_quests')
    op.drop_index(op.f('ix_user_quests_user_id'), table_name='user_quests')
    op.drop_index(op.f('ix_user_quests_id'), table_name='user_quests')
    op.drop_table('user_quests')
    op.drop_index(op.f('ix_quests_company_id'), table_name='quests')
    op.drop_index(op.f('ix_quests_event_id'), table_name='quests')
    op.drop_index(op.f('ix_quests_quest_type'), table_name='quests')
    op.drop_index(op.f('ix_quests_name'), table_name='quests')
    op.drop_index(op.f('ix_quests_id'), table_name='quests')
    op.drop_table('quests')
    op.drop_index(op.f('ix_events_company_id'), table_name='events')
    op.drop_index(op.f('ix_events_end_date'), table_name='events')
    op.drop_index(op.f('ix_events_start_date'), table_name='events')
    op.drop_index(op.f('ix_events_status'), table_name='events')
    op.drop_index(op.f('ix_events_event_type'), table_name='events')
    op.drop_index(op.f('ix_events_name'), table_name='events')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')
    op.drop_index(op.f('ix_transactions_company_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_status'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_seller_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_buyer_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_listing_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_marketplace_listings_company_id'), table_name='marketplace_listings')
    op.drop_index(op.f('ix_marketplace_listings_status'), table_name='marketplace_listings')
    op.drop_index(op.f('ix_marketplace_listings_item_id'), table_name='marketplace_listings')
    op.drop_index(op.f('ix_marketplace_listings_listing_type'), table_name='marketplace_listings')
    op.drop_index(op.f('ix_marketplace_listings_seller_id'), table_name='marketplace_listings')
    op.drop_index(op.f('ix_marketplace_listings_id'), table_name='marketplace_listings')
    op.drop_table('marketplace_listings')
    op.drop_index(op.f('ix_currency_transactions_transaction_type'), table_name='currency_transactions')
    op.drop_index(op.f('ix_currency_transactions_user_currency_id'), table_name='currency_transactions')
    op.drop_index(op.f('ix_currency_transactions_id'), table_name='currency_transactions')
    op.drop_table('currency_transactions')
    op.drop_index(op.f('ix_user_currency_user_id'), table_name='user_currency')
    op.drop_index(op.f('ix_user_currency_id'), table_name='user_currency')
    op.drop_table('user_currency')
    op.drop_index(op.f('ix_user_avatars_user_id'), table_name='user_avatars')
    op.drop_index(op.f('ix_user_avatars_id'), table_name='user_avatars')
    op.drop_table('user_avatars')
    op.drop_index(op.f('ix_cosmetic_crafting_requirements_cosmetic_id'), table_name='cosmetic_crafting_requirements')
    op.drop_index(op.f('ix_cosmetic_crafting_requirements_id'), table_name='cosmetic_crafting_requirements')
    op.drop_table('cosmetic_crafting_requirements')
    op.drop_index(op.f('ix_user_cosmetics_company_id'), table_name='user_cosmetics')
    op.drop_index(op.f('ix_user_cosmetics_obtained_at'), table_name='user_cosmetics')
    op.drop_index(op.f('ix_user_cosmetics_cosmetic_id'), table_name='user_cosmetics')
    op.drop_index(op.f('ix_user_cosmetics_user_id'), table_name='user_cosmetics')
    op.drop_index(op.f('ix_user_cosmetics_id'), table_name='user_cosmetics')
    op.drop_table('user_cosmetics')
    op.drop_index(op.f('ix_cosmetics_company_id'), table_name='cosmetics')
    op.drop_index(op.f('ix_cosmetics_rarity'), table_name='cosmetics')
    op.drop_index(op.f('ix_cosmetics_cosmetic_type'), table_name='cosmetics')
    op.drop_index(op.f('ix_cosmetics_name'), table_name='cosmetics')
    op.drop_index(op.f('ix_cosmetics_id'), table_name='cosmetics')
    op.drop_table('cosmetics')
    op.drop_index(op.f('ix_artifact_crafting_requirements_required_artifact_id'), table_name='artifact_crafting_requirements')
    op.drop_index(op.f('ix_artifact_crafting_requirements_artifact_id'), table_name='artifact_crafting_requirements')
    op.drop_index(op.f('ix_artifact_crafting_requirements_id'), table_name='artifact_crafting_requirements')
    op.drop_table('artifact_crafting_requirements')
    op.drop_index(op.f('ix_user_artifacts_company_id'), table_name='user_artifacts')
    op.drop_index(op.f('ix_user_artifacts_obtained_at'), table_name='user_artifacts')
    op.drop_index(op.f('ix_user_artifacts_artifact_id'), table_name='user_artifacts')
    op.drop_index(op.f('ix_user_artifacts_user_id'), table_name='user_artifacts')
    op.drop_index(op.f('ix_user_artifacts_id'), table_name='user_artifacts')
    op.drop_table('user_artifacts')
    op.drop_index(op.f('ix_artifacts_company_id'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_region_name'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_geozone_id'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_artifact_type'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_rarity'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_name'), table_name='artifacts')
    op.drop_index(op.f('ix_artifacts_id'), table_name='artifacts')
    op.drop_table('artifacts')
