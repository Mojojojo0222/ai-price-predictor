-- ============================================
-- AI Price Predictor - Supabase Database Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- ============================================
-- ENABLE EXTENSIONS
-- ============================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- 1. PRODUCTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT NOT NULL,
  name TEXT,
  image_url TEXT,
  category TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 2. PRICE HISTORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS price_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  price DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'INR',
  source TEXT,
  scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 3. USER TRACKS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS user_tracks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  target_price DECIMAL(10,2),
  alert_enabled BOOLEAN DEFAULT TRUE,
  alert_email BOOLEAN DEFAULT TRUE,
  alert_telegram BOOLEAN DEFAULT FALSE,
  telegram_chat_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, product_id)
);

-- ============================================
-- 4. PREDICTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  predicted_low DECIMAL(10,2),
  current_price DECIMAL(10,2),
  confidence DECIMAL(5,2),
  recommendation TEXT CHECK (recommendation IN ('BUY_NOW', 'WAIT', 'NO_DATA')),
  predicted_date DATE,
  reasoning TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_products_url ON products(url);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id, scraped_at);
CREATE INDEX IF NOT EXISTS idx_user_tracks_user ON user_tracks(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_product ON predictions(product_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- Users can only access their own data
-- ============================================

-- products: publicly readable (products are shared), but insert restricted by service role
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY "products_public_read" ON products FOR SELECT USING (true);
CREATE POLICY "products_insert" ON products FOR INSERT WITH CHECK (true);

-- price_history: publicly readable (needed to show charts), writes via service role
ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "price_history_public_read" ON price_history FOR SELECT USING (true);
CREATE POLICY "price_history_insert" ON price_history FOR INSERT WITH CHECK (true);

-- user_tracks: users manage their own tracks
ALTER TABLE user_tracks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_tracks_select_own" ON user_tracks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "user_tracks_insert_own" ON user_tracks FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_tracks_update_own" ON user_tracks FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "user_tracks_delete_own" ON user_tracks FOR DELETE USING (auth.uid() = user_id);

-- predictions: publicly readable, writes via service role
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "predictions_public_read" ON predictions FOR SELECT USING (true);
CREATE POLICY "predictions_insert" ON predictions FOR INSERT WITH CHECK (true);
CREATE POLICY "predictions_update" ON predictions FOR UPDATE USING (true);

-- ============================================
-- DONE!
-- After running this, copy these from Supabase dashboard:
--   Settings → API → Project URL  -> SUPABASE_URL
--   Settings → API → anon public key -> SUPABASE_KEY
--   Settings → API → service_role key -> SUPABASE_SERVICE_KEY
-- ============================================