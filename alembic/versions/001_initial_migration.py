"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_company_id'), 'users', ['company_id'], unique=False)

    # Создание таблицы geozones
    op.create_table(
        'geozones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('polygon', Geometry(geometry_type='POLYGON', srid=4326), nullable=False),
        sa.Column('center_latitude', sa.String(length=50), nullable=False),
        sa.Column('center_longitude', sa.String(length=50), nullable=False),
        sa.Column('radius_meters', sa.Integer(), nullable=True),
        sa.Column('geozone_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_geozones_id'), 'geozones', ['id'], unique=False)
    op.create_index(op.f('ix_geozones_name'), 'geozones', ['name'], unique=False)
    op.create_index(op.f('ix_geozones_geozone_type'), 'geozones', ['geozone_type'], unique=False)
    op.create_index(op.f('ix_geozones_company_id'), 'geozones', ['company_id'], unique=False)
    op.create_index('idx_geozone_polygon', 'geozones', ['polygon'], unique=False, postgresql_using='gist')

    # Создание таблицы location_sessions
    op.create_table(
        'location_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_started_at', sa.DateTime(), nullable=False),
        sa.Column('session_ended_at', sa.DateTime(), nullable=True),
        sa.Column('is_background', sa.Boolean(), nullable=False),
        sa.Column('is_offline', sa.Boolean(), nullable=False),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_sessions_id'), 'location_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_location_sessions_user_id'), 'location_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_location_sessions_session_started_at'), 'location_sessions', ['session_started_at'], unique=False)
    op.create_index(op.f('ix_location_sessions_company_id'), 'location_sessions', ['company_id'], unique=False)

    # Создание таблицы location_points
    op.create_table(
        'location_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('point', Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('accuracy_meters', sa.Float(), nullable=True),
        sa.Column('altitude_meters', sa.Float(), nullable=True),
        sa.Column('speed_ms', sa.Float(), nullable=True),
        sa.Column('heading_degrees', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('is_spoofed', sa.Boolean(), nullable=False),
        sa.Column('spoofing_score', sa.Float(), nullable=True),
        sa.Column('spoofing_reason', sa.String(length=255), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['location_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_points_id'), 'location_points', ['id'], unique=False)
    op.create_index(op.f('ix_location_points_session_id'), 'location_points', ['session_id'], unique=False)
    op.create_index(op.f('ix_location_points_timestamp'), 'location_points', ['timestamp'], unique=False)
    op.create_index(op.f('ix_location_points_company_id'), 'location_points', ['company_id'], unique=False)
    op.create_index('idx_location_point', 'location_points', ['point'], unique=False, postgresql_using='gist')

    # Создание таблицы geozone_visits
    op.create_table(
        'geozone_visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('geozone_id', sa.Integer(), nullable=False),
        sa.Column('visit_started_at', sa.DateTime(), nullable=False),
        sa.Column('visit_ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('verification_score', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['geozone_id'], ['geozones.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_geozone_visits_id'), 'geozone_visits', ['id'], unique=False)
    op.create_index(op.f('ix_geozone_visits_user_id'), 'geozone_visits', ['user_id'], unique=False)
    op.create_index(op.f('ix_geozone_visits_geozone_id'), 'geozone_visits', ['geozone_id'], unique=False)
    op.create_index(op.f('ix_geozone_visits_visit_started_at'), 'geozone_visits', ['visit_started_at'], unique=False)
    op.create_index(op.f('ix_geozone_visits_company_id'), 'geozone_visits', ['company_id'], unique=False)

    # Создание таблицы achievements
    op.create_table(
        'achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('achievement_type', sa.String(length=50), nullable=False),
        sa.Column('requirement_value', sa.Integer(), nullable=True),
        sa.Column('geozone_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['geozone_id'], ['geozones.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_achievements_id'), 'achievements', ['id'], unique=False)
    op.create_index(op.f('ix_achievements_name'), 'achievements', ['name'], unique=False)
    op.create_index(op.f('ix_achievements_achievement_type'), 'achievements', ['achievement_type'], unique=False)
    op.create_index(op.f('ix_achievements_company_id'), 'achievements', ['company_id'], unique=False)

    # Создание таблицы user_achievements
    op.create_table(
        'user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=False),
        sa.Column('progress_value', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_achievements_id'), 'user_achievements', ['id'], unique=False)
    op.create_index(op.f('ix_user_achievements_user_id'), 'user_achievements', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_achievements_achievement_id'), 'user_achievements', ['achievement_id'], unique=False)
    op.create_index(op.f('ix_user_achievements_unlocked_at'), 'user_achievements', ['unlocked_at'], unique=False)
    op.create_index(op.f('ix_user_achievements_company_id'), 'user_achievements', ['company_id'], unique=False)

    # Создание таблицы user_home_work
    op.create_table(
        'user_home_work',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('location_type', sa.String(length=20), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('point', Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('radius_meters', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('total_visits', sa.Integer(), nullable=False),
        sa.Column('total_time_minutes', sa.Integer(), nullable=False),
        sa.Column('first_detected_at', sa.DateTime(), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_confirmed', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_home_work_id'), 'user_home_work', ['id'], unique=False)
    op.create_index(op.f('ix_user_home_work_user_id'), 'user_home_work', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_home_work_location_type'), 'user_home_work', ['location_type'], unique=False)
    op.create_index(op.f('ix_user_home_work_company_id'), 'user_home_work', ['company_id'], unique=False)
    op.create_index('idx_user_home_work_point', 'user_home_work', ['point'], unique=False, postgresql_using='gist')

    # Составные индексы для оптимизации запросов
    op.create_index('idx_user_company', 'users', ['id', 'company_id'], unique=False)
    op.create_index('idx_geozone_visit_user_geozone', 'geozone_visits', ['user_id', 'geozone_id'], unique=False)
    op.create_index('idx_location_type_user', 'user_home_work', ['location_type', 'user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_location_type_user', table_name='user_home_work')
    op.drop_index('idx_geozone_visit_user_geozone', table_name='geozone_visits')
    op.drop_index('idx_user_company', table_name='users')
    op.drop_index('idx_user_home_work_point', table_name='user_home_work')
    op.drop_index(op.f('ix_user_home_work_company_id'), table_name='user_home_work')
    op.drop_index(op.f('ix_user_home_work_location_type'), table_name='user_home_work')
    op.drop_index(op.f('ix_user_home_work_user_id'), table_name='user_home_work')
    op.drop_index(op.f('ix_user_home_work_id'), table_name='user_home_work')
    op.drop_table('user_home_work')
    op.drop_index(op.f('ix_user_achievements_company_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_unlocked_at'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_achievement_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_user_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_id'), table_name='user_achievements')
    op.drop_table('user_achievements')
    op.drop_index(op.f('ix_achievements_company_id'), table_name='achievements')
    op.drop_index(op.f('ix_achievements_achievement_type'), table_name='achievements')
    op.drop_index(op.f('ix_achievements_name'), table_name='achievements')
    op.drop_index(op.f('ix_achievements_id'), table_name='achievements')
    op.drop_table('achievements')
    op.drop_index(op.f('ix_geozone_visits_company_id'), table_name='geozone_visits')
    op.drop_index(op.f('ix_geozone_visits_visit_started_at'), table_name='geozone_visits')
    op.drop_index(op.f('ix_geozone_visits_geozone_id'), table_name='geozone_visits')
    op.drop_index(op.f('ix_geozone_visits_user_id'), table_name='geozone_visits')
    op.drop_index(op.f('ix_geozone_visits_id'), table_name='geozone_visits')
    op.drop_table('geozone_visits')
    op.drop_index('idx_location_point', table_name='location_points')
    op.drop_index(op.f('ix_location_points_company_id'), table_name='location_points')
    op.drop_index(op.f('ix_location_points_timestamp'), table_name='location_points')
    op.drop_index(op.f('ix_location_points_session_id'), table_name='location_points')
    op.drop_index(op.f('ix_location_points_id'), table_name='location_points')
    op.drop_table('location_points')
    op.drop_index(op.f('ix_location_sessions_company_id'), table_name='location_sessions')
    op.drop_index(op.f('ix_location_sessions_session_started_at'), table_name='location_sessions')
    op.drop_index(op.f('ix_location_sessions_user_id'), table_name='location_sessions')
    op.drop_index(op.f('ix_location_sessions_id'), table_name='location_sessions')
    op.drop_table('location_sessions')
    op.drop_index('idx_geozone_polygon', table_name='geozones')
    op.drop_index(op.f('ix_geozones_company_id'), table_name='geozones')
    op.drop_index(op.f('ix_geozones_geozone_type'), table_name='geozones')
    op.drop_index(op.f('ix_geozones_name'), table_name='geozones')
    op.drop_index(op.f('ix_geozones_id'), table_name='geozones')
    op.drop_table('geozones')
    op.drop_index(op.f('ix_users_company_id'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
