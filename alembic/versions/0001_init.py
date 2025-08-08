from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_ccn", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("zip", sa.String(), nullable=False),
        sa.Column("drg_code", sa.String(), nullable=False),
        sa.Column("drg_desc", sa.String(), nullable=False),
        sa.Column("average_covered_charges", sa.Float()),
        sa.Column("average_total_payments", sa.Float()),
        sa.Column("average_medicare_payments", sa.Float()),
        sa.Column("lat", sa.Float()),
        sa.Column("lon", sa.Float()),
    )
    op.create_index(
        "ix_providers_provider_ccn", "providers", ["provider_ccn"], unique=True
    )
    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "provider_ccn",
            sa.String(),
            sa.ForeignKey("providers.provider_ccn", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("ratings")
    op.drop_index("ix_providers_provider_ccn", table_name="providers")
    op.drop_table("providers")
