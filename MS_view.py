import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# 1. ページ設定
st.set_page_config(page_title="競馬分析ダッシュボード", layout="wide")

# ==========================================
# ★ここを表示したい日付に書き換えてください
DATE_VAL = "20260118" 
# ==========================================

# 場所マスター
PLACE_MASTER = {
    1: "札幌", 2: "函館", 3: "福島", 4: "新潟", 5: "東京",
    6: "中山", 7: "中京", 8: "京都", 9: "阪神", 10: "小倉"
}

# --- 色設定の関数 ---

# 判定(SS, S, A...)の色
def color_rank(val):
    # SS系統
    if val == 'SS':  return 'background-color: #ff69b4; color: white; font-weight: bold'
    if val == 'SS-': return 'background-color: #ff69b4; color: white'
    
    # S系統
    if val == 'S':   return 'background-color: #ff4500; color: white; font-weight: bold'
    if val == 'S-':  return 'background-color: #ff4500; color: white'
    
    # A系統
    if val == 'A':   return 'background-color: #ffa500; color: black; font-weight: bold'
    if val == 'A-':  return 'background-color: #ffa500; color: black'
    
    # B系統
    if val == 'B':   return 'background-color: #98fb98; color: black; font-weight: bold'
    if val == 'B-':  return 'background-color: #98fb98; color: black'
    
    # C系統 (追加)
    if val == 'C':   return 'background-color: #f0f8ff; color: black; font-weight: bold' # 薄い緑
    if val == 'C-':  return 'background-color: #f0f8ff; color: black'
    
    # D系統
    if val == 'D':   return 'background-color: #CCCCCC; color: black; font-weight: bold'
    if val == 'D-':  return 'background-color: #CCCCCC; color: black'
    
    # E系統
    if val == 'E':   return 'background-color: #AAAAAA; color: white; font-weight: bold'
    
    return ''

# 順位の色（1位: 黄, 2位: 水色, 3位: 黄緑, その他: 薄グレー）
def color_order(val):
    if val == 1: return 'background-color: #FFFF00; color: black; font-weight: bold' # 黄
    if val == 2: return 'background-color: #e0ffff; color: black; font-weight: bold' # 水色
    if val == 3: return 'background-color: #f8f8ff; color: black; font-weight: bold' # 黄緑
    if val == 4: return 'background-color: #f5f5dc; color: black; font-weight: bold' # 黄緑
    if val == 5: return 'background-color: #faf0e6; color: black; font-weight: bold' # 黄緑
    if val != "" and val != "-": return 'background-color: #F0F0F0; color: black' # 薄グレー
    return ''

# MS指数の色分け
def color_ms_index(val):
    try:
        v = float(val) if val != "-" else 0
    except: return ''
    if v >= 30.0: return 'background-color: #FF0000; color: white'
    if v >= 25.0: return 'background-color: #FF4500; color: white'
    if v >= 20.0: return 'background-color: #FF8C00; color: black'
    if v >= 15.0: return 'background-color: #FFD700; color: black'
    if v >= 10.0: return 'background-color: #FFFACD; color: black'
    return ''

# MSPF指数の色分け
def color_mspf_expect(val):
    try:
        v = float(val) if val != "-" else 0
    except: return ''
    if v >= 100.0: return 'background-color: #FF69B4; color: white' # ピンク系
    if v >= 98.0:  return 'background-color: #f4a460; color: black'
    if v >= 95.0:  return 'background-color: #f5deb3; color: black'
    return ''

# MST指数の色分け
def color_mst_index(val):
    try:
        v = float(val) if val != "-" else 0
    except: return ''
    if v >= 15.0: return 'background-color: #FFE4B5; color: black' # 薄オレンジ
    if v >= 10.0: return 'background-color: #FFFACD; color: black' # 薄黄色
    return ''

# ポイント定義
POINT_MAP = {'SS': 15, 'S': 12, 'A': 9, 'B': 7, 'C': 5, 'D': 3, 'E': 1}

# --- 判定ロジック ---

# 合計点からランク文字を出す
def get_al_rank(total_pt):
    if total_pt >= 28: return 'SS'
    if total_pt >= 27: return 'SS-'
    if total_pt >= 24: return 'S'
    if total_pt >= 21: return 'S-'
    if total_pt >= 18: return 'A'
    if total_pt >= 16: return 'A-'
    if total_pt >= 14: return 'B'
    if total_pt >= 12: return 'B-'
    if total_pt >= 10: return 'C'
    if total_pt >= 8:  return 'C-'
    if total_pt >= 6:  return 'D'
    if total_pt >= 4:  return 'D-'
    if total_pt >= 2:  return 'E'
    return ""

# MSとMSPFを合算して判定を出す（共通処理）
def get_combined_rank(ms_val, mspf_val, is_special=False):
    def get_pt(val):
        s_val = str(val).strip() if pd.notnull(val) else ""
        return POINT_MAP.get(s_val, 5) # 文字があればその点、なければC(5点)

    total = get_pt(ms_val) + get_pt(mspf_val)
    rank = get_al_rank(total)
    
    # CD, GR列のみ、C判定（10点）なら空欄にする
    if is_special and rank == 'C':
        return ""
    return rank



# --- データ読込 ---
@st.cache_data
def load_and_merge_data(date):

    
    base_dir = "data/"
    try:
        # 1. 既存データの読み込み
        df_mspf_ex = pd.read_csv(os.path.join(base_dir, f"MSPF_expect_results_{date}.csv"))
        df_ms_res = pd.read_csv(os.path.join(base_dir, f"MS_index_results_{date}.csv"))
        df_mst_res = pd.read_csv(os.path.join(base_dir, f"MST_index_results_{date}.csv"))
        
        # 【重要】既存データの型を確実に数値に変換（不一致防止）
        for target_df in [df_mspf_ex, df_ms_res, df_mst_res]:
            target_df['場所'] = target_df['場所'].astype(int)
            target_df['馬番'] = target_df['馬番'].astype(int)

        # --- ID形式のCSV読み込み内部関数 ---
        def load_id_csv(file_name, val_col_name):
            path = os.path.join(base_dir, file_name)
            if not os.path.exists(path):
                return pd.DataFrame()
            
            # ヘッダーなしCSVを読み込み
            tmp = pd.read_csv(path, header=None, names=['ID', val_col_name], dtype={'ID': str})
            
            # IDからキーを抽出
            # IDから直接文字を抜き出す
            tmp['場所'] = tmp['ID'].str[8:10].astype(int)
            tmp['レース'] = tmp['ID'].str[8:10] + "_" + tmp['ID'].str[14:16].astype(str).str.lstrip('0').str.zfill(1) # 10以下を1桁にする
            tmp['馬番'] = tmp['ID'].str[16:18].astype(int)
            
            
            return tmp[['場所', 'レース', '馬番', val_col_name]]

        # 2. 新しい MS_日付.csv / MSPF_日付.csv を読み込む
        df_new_ms = load_id_csv(f"MS_{date}.csv", "MS_val")
        df_new_mspf = load_id_csv(f"MSPF_{date}.csv", "MSPF_val")

        # 3. 既存データの準備（総合判定などを結合用にする）
        ms_cols = {df_ms_res.columns[8]: '総合判定_MS', 'MS_index': 'MS_index_MS'}
        df_ms_sub = df_ms_res[['場所', 'レース', '馬番'] + list(ms_cols.keys())].rename(columns=ms_cols)

        # 4. ベースデータに既存結果を結合
        df = df_mspf_ex.merge(df_ms_sub, on=['場所', 'レース', '馬番'], how='left')
        df = df.merge(df_mst_res[['場所', 'レース', '馬番', 'MS_index']], on=['場所', 'レース', '馬番'], how='left')
        df = df.rename(columns={'MS_index': 'MST_index'})
        
        # 5. 今回の新しい数値を結合（型の不一致を排除して結合）
        if not df_new_ms.empty:
            df = df.merge(df_new_ms, on=['場所', 'レース', '馬番'], how='left')
        if not df_new_mspf.empty:
            df = df.merge(df_new_mspf, on=['場所', 'レース', '馬番'], how='left')

        # --- 重複を排除するコードを追加 ---
        df = df.drop_duplicates(subset=['場所', 'レース', '馬番'], keep='first')
            
        return df

    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")
        return None


# --- メイン処理 ---
try:
    dt = datetime.strptime(DATE_VAL, '%Y%m%d')
    DATE_STR = dt.strftime('%Y年%m月%d日')
except Exception:
    DATE_STR = DATE_VAL

# タイトルと日付の表示
st.title("🏇 競馬指数ダッシュボード")
st.markdown(f"### 📅 {DATE_STR}")
st.divider()

# データロード
df_raw = load_and_merge_data(DATE_VAL)



if df_raw is not None:
    df_raw['場所名'] = df_raw['場所'].map(PLACE_MASTER).fillna(df_raw['場所'])
    all_places = sorted(df_raw['場所名'].unique())
    
    selected_place = st.pills("場所：", options=all_places, selection_mode="single", default=all_places[0])
    
    if selected_place:
        race_codes = sorted(df_raw[df_raw['場所名'] == selected_place]['レース'].unique(), key=lambda x: int(x.split('_')[1]))
        race_display_names = [f"{c.split('_')[1]}R" for c in race_codes]
        race_map = dict(zip(race_display_names, race_codes))
        selected_race_name = st.pills("R：", options=race_display_names, selection_mode="single", default=race_display_names[0])
        
        if selected_race_name:
            current_race_code = race_map[selected_race_name]
            st.subheader(f"🚩 {selected_place} {selected_race_name}")
            df_race = df_raw[(df_raw['場所名'] == selected_place) & (df_raw['レース'] == current_race_code)].copy()

            # 1. 順位計算（新しく読み込んだ MS_val, MSPF_val を使う）
            rank_targets = [
                ('MS_val', 'MS順'), ('MSPF_val', 'MSPF順'), 
                ('MS_index_MS', 'nMS順'), ('MSPF_expect', 'nMSPF順'), ('MST_index', 'nMST順')
            ]
            for col, new_col in rank_targets:
                if col in df_race.columns:
                    df_race[new_col] = df_race[col].rank(ascending=False, method='min').fillna(99).astype(int)

            # 2. 全列合算判定
            df_race['AL'] = df_race.apply(lambda r: get_combined_rank(r.get('総合判定_MS'), r.get('総合判定')), axis=1)

            # 3. 表示整形（★ここが重要：MS_val を MS という名前に変換する）
            display_cols_map = {
                '馬番': '馬番', '馬名': '馬名', 
                'MS_val': 'MS',           # ← 読み込んだ MS_val を表示名 MS に
                'MS順': ' ', 
                'MSPF_val': 'MSPF',       # ← 読み込んだ MSPF_val を表示名 MSPF に
                'MSPF順': '  ',
                'MS_index_MS': 'newMS', 'nMS順': '   ', 
                'MSPF_expect': 'newMSPF', 'nMSPF順': '    ', 
                'MST_index': 'newMST', 'nMST順': '     '
            }
            
            available_cols = [c for c in display_cols_map.keys() if c in df_race.columns]
            df_display = df_race[available_cols].rename(columns=display_cols_map)

            # 4. 数値クレンジング（MS と MSPF も対象に含める）
            target_num_cols = ['MS', 'MSPF', 'newMS', 'newMSPF', 'newMST']
            for c in target_num_cols:
                if c in df_display.columns:
                    df_display[c] = pd.to_numeric(df_display[c], errors='coerce')
                    df_display[c] = df_display[c].apply(
                        lambda x: f"{x:.1f}" if pd.notnull(x) else "-"
                    )
            
            # 5. スタイリング
            rank_cols = [' ', '  ', '   ', '    ', '     ']
            styled_df = df_display.style\
                .map(color_order, subset=[c for c in rank_cols if c in df_display.columns])\
                .map(color_ms_index, subset=[c for c in ['MS'] if c in df_display.columns])\
                .map(color_mspf_expect, subset=[c for c in ['MSPF'] if c in df_display.columns])\
                .set_properties(subset=[c for c in ['newMS', 'newMSPF', 'newMST'] if c in df_display.columns], 
                               **{'background-color': '#F0F0F0', 'color': 'black'})\
            
            # 列の幅を個別に設定
            col_config = {
                "馬番": st.column_config.Column(width=45),
                "馬名": st.column_config.Column(width=180),
                "MS": st.column_config.Column(width=45),
                "MSPF": st.column_config.Column(width=45),
                # 順位の列（スペースの数に注意）
                " ": st.column_config.Column(width=30),
                "  ": st.column_config.Column(width=30),
            }
            
            st.dataframe(
                styled_df, 
                height=750, 
                use_container_width=True, 
                hide_index=True,
                column_config=col_config  # ← ここで設定を反映
            )

            # --- ここから期待値表の表示コード ---
            st.divider()
            st.markdown("### 📊 MS指数 期待値統計")

            # 統計データの定義（数値を小数点第1位の文字列で固定）
            data_shiba = {
                "min": ["50.1", "45.1", "40.1", "35.1", "30.1", "25.1", "20.1", "15.1", "10.1", "5.1", "0.2", "0.1"],
                "max": ["99.9", "50.0", "45.0", "40.0", "35.0", "30.0", "25.0", "20.0", "15.0", "10.0", "5.0", "0.1"],
                "勝率": ["32.3%", "33.3%", "40.8%", "34.5%", "28.0%", "31.6%", "23.0%", "17.0%", "12.2%", "6.5%", "3.1%", "1.6%"],
                "連対率": ["67.7%", "63.6%", "61.2%", "58.3%", "47.8%", "53.6%", "40.5%", "31.8%", "24.0%", "14.1%", "6.7%", "4.1%"],
                "複勝率": ["83.9%", "69.7%", "77.6%", "77.4%", "61.8%", "70.7%", "53.1%", "45.2%", "35.6%", "22.0%", "11.1%", "6.8%"]
            }
            data_dirt = {
                "min": ["50.1", "45.1", "40.1", "35.1", "30.1", "25.1", "20.1", "15.1", "10.1", "5.1", "0.2", "0.1"],
                "max": ["99.9", "50.0", "45.0", "40.0", "35.0", "30.0", "25.0", "20.0", "15.0", "10.0", "5.0", "0.1"],
                "勝率": ["63.6%", "37.5%", "34.9%", "40.2%", "36.7%", "25.0%", "25.3%", "17.8%", "12.3%", "6.4%", "2.5%", "1.7%"],
                "連対率": ["72.7%", "68.8%", "60.5%", "61.0%", "54.7%", "43.0%", "43.7%", "32.7%", "24.9%", "13.5%", "6.1%", "3.7%"],
                "複勝率": ["77.3%", "87.5%", "74.4%", "67.1%", "65.6%", "58.5%", "56.8%", "44.1%", "35.3%", "21.6%", "10.6%", "6.9%"]
            }

            # 2カラムで横並びに表示
            col_shiba, col_dirt = st.columns(2)
            
            with col_shiba:
                st.markdown("**🍀 MS 芝**")
                st.table(pd.DataFrame(data_shiba))
                
            with col_dirt:
                st.markdown("**🏜️ MS ダート**")
                st.table(pd.DataFrame(data_dirt))
else:

    st.error("データが見つかりません。")












