# profit_doctor.py

import pandas as pd
import numpy as np
from dataclasses import dataclass
from config import CFG


@dataclass
class ProfitDoctorAgent:
    """
    Agent 2: Profit Doctor (OPTIMIZED)

    Responsibilities:
    - Compute Effective Selling Price
    - Compute payment gateway fees + GST
    - Allocate ad cost per unit
    - Compute Profit Per Unit
    - Compute Loss Per Day for negative-margin SKUs
    
    Performance Improvements:
    - Chained operations to reduce intermediate DataFrames
    - Optimized division-by-zero handling
    - Single DataFrame copy at start
    - Vectorized all operations
    """

    fee_gst_rate: float = CFG.fee_gst_rate

    def compute_profit_metrics(self, df_master: pd.DataFrame) -> pd.DataFrame:
        """
        OPTIMIZED: All operations vectorized with minimal copies.
        """
        # Single copy at the start
        df = df_master.copy()

        # 1) Discount / Effective Selling Price (vectorized)
        if "mrp" in df.columns:
            df["discount_applied"] = np.maximum(df["mrp"] - df["selling_price"], 0.0)
        else:
            df["discount_applied"] = 0.0

        df["effective_selling_price"] = df["selling_price"] - df["discount_applied"]

        # 2) Payment fees + GST on fees (vectorized, chained)
        df["payment_fee"] = (
            (df["platform_fee_percent"] / 100.0) * df["effective_selling_price"]
            + df["platform_fixed_fee"]
        )
        df["fee_gst"] = self.fee_gst_rate * df["payment_fee"]
        df["total_fees"] = df["payment_fee"] + df["fee_gst"]

        # 3) Ad cost per unit (optimized division-by-zero handling)
        # Use np.divide with where parameter for efficiency
        df["ad_cost_per_unit"] = np.divide(
            df["ad_spend_total_last_30_days"],
            df["units_sold_last_30_days"],
            out=np.zeros_like(df["ad_spend_total_last_30_days"], dtype=float),
            where=df["units_sold_last_30_days"] > 0
        )

        # 4) Profit per unit (vectorized)
        df["profit_per_unit"] = (
            df["effective_selling_price"]
            - df["cogs"]
            - df["total_fees"]
            - df["ad_cost_per_unit"]
            - df["shipping_cost_per_unit"]
        )

        # 5) Units sold per day (vectorized)
        df["units_sold_per_day"] = df["units_sold_last_30_days"] / 30.0

        # 6) Loss per day for negative-margin SKUs (vectorized)
        is_loss = df["profit_per_unit"] < 0
        df["loss_per_day"] = np.where(
            is_loss,
            np.abs(df["profit_per_unit"]) * df["units_sold_per_day"],
            0.0
        )
        df["is_loss_maker"] = is_loss

        return df
