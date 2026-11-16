CREATE TABLE IF NOT EXISTS transactions (
  txn_id TEXT PRIMARY KEY,
  merchant_id TEXT,
  amount NUMERIC(12,3),
  currency TEXT DEFAULT 'KWD',
  gateway TEXT,
  gateway_status TEXT,
  ledger_status TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO transactions VALUES
('TXN1001','M001',25.500,'KWD','KNET','CAPTURED','POSTED',now()),
('TXN1002','M001',12.000,'KWD','KNET','CAPTURED','PENDING',now()),
('TXN1003','M002',150.750,'KWD','MPGS','FAILED','POSTED',now()),
('TXN1004','M002',8.250,'KWD','APPLE_PAY','CAPTURED','POSTED',now())
ON CONFLICT DO NOTHING;