"""create code_dependencies change_audit_log test_execution_log

Revision ID: a3f8c2e1d4b7
Revises: 74a54b915235
Create Date: 2026-08-24 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f8c2e1d4b7'
down_revision: Union[str, None] = '74a54b915235'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── code_dependencies ──────────────────────────────────────────────
    op.create_table(
        'code_dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('source_file_id', sa.Integer(), nullable=False),
        sa.Column('target_file_id', sa.Integer(), nullable=True),
        sa.Column('target_module', sa.String(length=500), nullable=True),
        sa.Column('dependency_type', sa.String(length=50), nullable=False),
        sa.Column('symbol_name', sa.String(length=255), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_file_id'], ['files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_file_id'], ['files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_code_dependencies_id', 'code_dependencies', ['id'], unique=False)
    op.create_index('ix_code_dependencies_repository_id', 'code_dependencies', ['repository_id'], unique=False)
    op.create_index('ix_code_dependencies_source_file_id', 'code_dependencies', ['source_file_id'], unique=False)
    op.create_index('ix_code_dependencies_target_file_id', 'code_dependencies', ['target_file_id'], unique=False)

    # ── change_audit_log ───────────────────────────────────────────────
    op.create_table(
        'change_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('user_request', sa.Text(), nullable=False),
        sa.Column('plan_summary', sa.Text(), nullable=True),
        sa.Column('target_files', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('branch_name', sa.String(length=255), nullable=True),
        sa.Column('commit_sha', sa.String(length=64), nullable=True),
        sa.Column('push_status', sa.String(length=20), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=True),
        sa.Column('pr_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id'),
    )
    op.create_index('ix_change_audit_log_id', 'change_audit_log', ['id'], unique=False)
    op.create_index('ix_change_audit_log_plan_id', 'change_audit_log', ['plan_id'], unique=False)
    op.create_index('ix_change_audit_log_project_id', 'change_audit_log', ['project_id'], unique=False)
    op.create_index('ix_change_audit_log_repository_id', 'change_audit_log', ['repository_id'], unique=False)

    # ── test_execution_log ─────────────────────────────────────────────
    op.create_table(
        'test_execution_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('framework', sa.String(length=50), nullable=True),
        sa.Column('tests_selected', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('tests_run', sa.Integer(), nullable=True),
        sa.Column('tests_failed', sa.Integer(), nullable=True),
        sa.Column('stdout_snippet', sa.Text(), nullable=True),
        sa.Column('stderr_snippet', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_test_execution_log_id', 'test_execution_log', ['id'], unique=False)
    op.create_index('ix_test_execution_log_plan_id', 'test_execution_log', ['plan_id'], unique=False)
    op.create_index('ix_test_execution_log_project_id', 'test_execution_log', ['project_id'], unique=False)
    op.create_index('ix_test_execution_log_repository_id', 'test_execution_log', ['repository_id'], unique=False)


def downgrade() -> None:
    op.drop_table('test_execution_log')
    op.drop_table('change_audit_log')
    op.drop_table('code_dependencies')
