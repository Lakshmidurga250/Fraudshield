from flask_wtf import FlaskForm
from wtforms import DecimalField, FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class TransactionAssessmentForm(FlaskForm):
    """Transaction assessment input form with numeric validation."""

    amount = DecimalField(
        "Transaction Amount ($)",
        validators=[
            DataRequired(message="Transaction amount is required."),
            NumberRange(
                min=0.01, max=1000000.0, message="Amount must be between 0.01 and 1,000,000.00."
            ),
        ],
        places=2,
        default=45.00,
    )
    time_val = FloatField(
        "Transaction Elapsed Time (seconds)",
        validators=[NumberRange(min=0.0, message="Time must be non-negative.")],
        default=3600.0,
    )
    decision_threshold = FloatField(
        "Decision Threshold",
        validators=[
            NumberRange(min=0.05, max=0.95, message="Threshold must be between 0.05 and 0.95.")
        ],
        default=0.50,
    )

    # PCA Features V1 through V28
    v1 = FloatField("V1", default=0.0)
    v2 = FloatField("V2", default=0.0)
    v3 = FloatField("V3", default=0.0)
    v4 = FloatField("V4", default=0.0)
    v5 = FloatField("V5", default=0.0)
    v6 = FloatField("V6", default=0.0)
    v7 = FloatField("V7", default=0.0)
    v8 = FloatField("V8", default=0.0)
    v9 = FloatField("V9", default=0.0)
    v10 = FloatField("V10", default=0.0)
    v11 = FloatField("V11", default=0.0)
    v12 = FloatField("V12", default=0.0)
    v13 = FloatField("V13", default=0.0)
    v14 = FloatField("V14", default=0.0)
    v15 = FloatField("V15", default=0.0)
    v16 = FloatField("V16", default=0.0)
    v17 = FloatField("V17", default=0.0)
    v18 = FloatField("V18", default=0.0)
    v19 = FloatField("V19", default=0.0)
    v20 = FloatField("V20", default=0.0)
    v21 = FloatField("V21", default=0.0)
    v22 = FloatField("V22", default=0.0)
    v23 = FloatField("V23", default=0.0)
    v24 = FloatField("V24", default=0.0)
    v25 = FloatField("V25", default=0.0)
    v26 = FloatField("V26", default=0.0)
    v27 = FloatField("V27", default=0.0)
    v28 = FloatField("V28", default=0.0)

    submit = SubmitField("Evaluate Transaction Risk")
