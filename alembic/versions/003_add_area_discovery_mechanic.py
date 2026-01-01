"""Add area discovery mechanic

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем новые поля в таблицу geozones для поддержки Area POI
    op.add_column('geozones', sa.Column('area_type', sa.String(length=50), nullable=True))
    op.add_column('geozones', sa.Column('area_square_meters', sa.Float(), nullable=True))
    op.add_column('geozones', sa.Column('osm_id', sa.String(length=100), nullable=True))
    op.add_column('geozones', sa.Column('osm_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    op.create_index(op.f('ix_geozones_area_type'), 'geozones', ['area_type'], unique=False)
    op.create_index(op.f('ix_geozones_osm_id'), 'geozones', ['osm_id'], unique=False)
    
    # Создаём таблицу area_discoveries для отслеживания открытия областей
    op.create_table(
        'area_discoveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('geozone_id', sa.Integer(), nullable=False),
        sa.Column('discovery_status', sa.String(length=20), nullable=False, server_default='discovered'),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('area_covered_meters', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('first_discovered_at', sa.DateTime(), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['geozone_id'], ['geozones.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_area_discoveries_id'), 'area_discoveries', ['id'], unique=False)
    op.create_index(op.f('ix_area_discoveries_user_id'), 'area_discoveries', ['user_id'], unique=False)
    op.create_index(op.f('ix_area_discoveries_geozone_id'), 'area_discoveries', ['geozone_id'], unique=False)
    op.create_index(op.f('ix_area_discoveries_discovery_status'), 'area_discoveries', ['discovery_status'], unique=False)
    op.create_index(op.f('ix_area_discoveries_first_discovered_at'), 'area_discoveries', ['first_discovered_at'], unique=False)
    op.create_index(op.f('ix_area_discoveries_last_updated_at'), 'area_discoveries', ['last_updated_at'], unique=False)


def downgrade() -> None:
    # Удаляем таблицу area_discoveries
    op.drop_index(op.f('ix_area_discoveries_last_updated_at'), table_name='area_discoveries')
    op.drop_index(op.f('ix_area_discoveries_first_discovered_at'), table_name='area_discoveries')
    op.drop_index(op.f('ix_area_discoveries_discovery_status'), table_name='area_discoveries')
    op.drop_index(op.f('ix_area_discoveries_geozone_id'), table_name='area_discoveries')
    op.drop_index(op.f('ix_area_discoveries_user_id'), table_name='area_discoveries')
    op.drop_index(op.f('ix_area_discoveries_id'), table_name='area_discoveries')
    op.drop_table('area_discoveries')
    
    # Удаляем индексы и поля из geozones
    op.drop_index(op.f('ix_geozones_osm_id'), table_name='geozones')
    op.drop_index(op.f('ix_geozones_area_type'), table_name='geozones')
    op.drop_column('geozones', 'osm_tags')
    op.drop_column('geozones', 'osm_id')
    op.drop_column('geozones', 'area_square_meters')
    op.drop_column('geozones', 'area_type')
