import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# ページ設定
st.set_page_config(
    page_title="EC売上分析ダッシュボード",
    page_icon="📊",
    layout="wide"
)

# タイトル
st.title("EC売上分析ダッシュボード")

# データ読み込み
@st.cache_data
def load_data():
    df = pd.read_csv('data/sample-data.csv')
    # 日付列を datetime に変換
    df['購入日'] = pd.to_datetime(df['購入日'])
    return df

df = load_data()

# サイドバーのフィルター
st.sidebar.header('データフィルター')

# 日付範囲フィルター
min_date = df['購入日'].min()
max_date = df['購入日'].max()
date_range = st.sidebar.date_input(
    "期間を選択",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# カテゴリーフィルター
categories = ['すべて'] + list(df['購入カテゴリー'].unique())
selected_category = st.sidebar.selectbox('カテゴリーを選択', categories)

# データのフィルタリング
if len(date_range) == 2:
    mask = (df['購入日'].dt.date >= date_range[0]) & (df['購入日'].dt.date <= date_range[1])
    df_filtered = df[mask].copy()
else:
    df_filtered = df.copy()

if selected_category != 'すべて':
    df_filtered = df_filtered[df_filtered['購入カテゴリー'] == selected_category].copy()

# メインコンテンツ
# 1. 概要指標（Key Metrics）
st.header('1. 概要指標')
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "総売上金額",
        f"¥{df_filtered['購入金額'].sum():,.0f}"
    )

with col2:
    st.metric(
        "総注文件数",
        f"{len(df_filtered):,}件"
    )

with col3:
    st.metric(
        "平均購入金額",
        f"¥{df_filtered['購入金額'].mean():,.0f}"
    )

with col4:
    st.metric(
        "ユニーク顧客数",
        f"{df_filtered['顧客ID'].nunique():,}人"
    )

# 2. 時系列分析
st.header('2. 時系列分析')
tab1, tab2, tab3 = st.tabs(["売上推移", "曜日・月別分析", "ヒートマップ"])

with tab1:
    # 月次売上推移グラフ（移動平均線付き）
    monthly_sales = df_filtered.groupby(df_filtered['購入日'].dt.strftime('%Y-%m'))[['購入金額']].sum().reset_index()
    monthly_sales['移動平均'] = monthly_sales['購入金額'].rolling(window=3).mean()
    
    fig_monthly = go.Figure()
    fig_monthly.add_trace(
        go.Scatter(
            x=monthly_sales['購入日'],
            y=monthly_sales['購入金額'],
            name='売上金額',
            line=dict(color='#1f77b4')
        )
    )
    fig_monthly.add_trace(
        go.Scatter(
            x=monthly_sales['購入日'],
            y=monthly_sales['移動平均'],
            name='3ヶ月移動平均',
            line=dict(color='#ff7f0e', dash='dash')
        )
    )
    fig_monthly.update_layout(
        title='月次売上推移（3ヶ月移動平均付き）',
        xaxis_title='年月',
        yaxis_title='売上金額',
        hovermode='x unified'
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

    # 日次売上推移グラフ
    daily_sales = df_filtered.groupby('購入日')[['購入金額']].sum().reset_index()
    daily_sales['移動平均'] = daily_sales['購入金額'].rolling(window=7).mean()
    
    fig_daily = go.Figure()
    fig_daily.add_trace(
        go.Scatter(
            x=daily_sales['購入日'],
            y=daily_sales['購入金額'],
            name='売上金額',
            line=dict(color='#1f77b4')
        )
    )
    fig_daily.add_trace(
        go.Scatter(
            x=daily_sales['購入日'],
            y=daily_sales['移動平均'],
            name='7日移動平均',
            line=dict(color='#ff7f0e', dash='dash')
        )
    )
    fig_daily.update_layout(
        title='日次売上推移（7日移動平均付き）',
        xaxis_title='日付',
        yaxis_title='売上金額',
        hovermode='x unified'
    )
    st.plotly_chart(fig_daily, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # 曜日別売上分布
        df_filtered['曜日'] = df_filtered['購入日'].dt.day_name()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_japanese = {'Monday': '月曜日', 'Tuesday': '火曜日', 'Wednesday': '水曜日',
                          'Thursday': '木曜日', 'Friday': '金曜日', 'Saturday': '土曜日',
                          'Sunday': '日曜日'}
        
        weekday_sales = df_filtered.groupby('曜日')['購入金額'].agg(['sum', 'count']).reset_index()
        weekday_sales['曜日'] = weekday_sales['曜日'].map(weekday_japanese)
        weekday_sales = weekday_sales.sort_values('曜日', key=lambda x: pd.Categorical(
            x.map({v: k for k, v in weekday_japanese.items()}), 
            categories=weekday_order, 
            ordered=True
        ))
        
        fig_weekday = px.bar(
            weekday_sales,
            x='曜日',
            y='sum',
            title='曜日別売上金額',
            labels={'sum': '売上金額', '曜日': ''},
            text=weekday_sales['count'].apply(lambda x: f'{x}件')
        )
        fig_weekday.update_traces(textposition='outside')
        st.plotly_chart(fig_weekday, use_container_width=True)
    
    with col2:
        # 月別売上分布
        df_filtered['月'] = df_filtered['購入日'].dt.month
        monthly_distribution = df_filtered.groupby('月')['購入金額'].agg(['sum', 'count']).reset_index()
        monthly_distribution['月'] = monthly_distribution['月'].apply(lambda x: f'{x}月')
        
        fig_monthly_dist = px.bar(
            monthly_distribution,
            x='月',
            y='sum',
            title='月別売上金額',
            labels={'sum': '売上金額', '月': ''},
            text=monthly_distribution['count'].apply(lambda x: f'{x}件')
        )
        fig_monthly_dist.update_traces(textposition='outside')
        st.plotly_chart(fig_monthly_dist, use_container_width=True)

with tab3:
    # 時間帯×曜日のヒートマップ
    df_filtered.loc[:, '時間帯'] = df_filtered['購入日'].dt.hour
    df_filtered.loc[:, '曜日'] = df_filtered['購入日'].dt.day_name()
    
    # ピボットテーブルの作成
    heatmap_data = pd.pivot_table(
        df_filtered,
        values='購入金額',
        index='時間帯',
        columns='曜日',
        aggfunc='sum',
        fill_value=0
    )
    
    # 曜日の順序を設定
    heatmap_data = heatmap_data.reindex(columns=weekday_order)
    
    # 日本語の曜日名に変更
    heatmap_data.columns = [weekday_japanese[day] for day in heatmap_data.columns]
    
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x='曜日', y='時間帯', color='売上金額'),
        title='時間帯×曜日別の売上金額ヒートマップ',
        color_continuous_scale='Blues'
    )
    
    fig_heatmap.update_layout(
        xaxis_title='',
        yaxis_title='時間帯'
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)

# 3. 顧客分析
st.header('3. 顧客分析')
col1, col2 = st.columns(2)

with col1:
    # 年齢層別の購入分布
    age_bins = [0, 20, 30, 40, 50, 60, 70, 100]
    age_labels = ['20歳未満', '20-30歳', '31-40歳', '41-50歳', '51-60歳', '61-70歳', '71歳以上']
    df_filtered.loc[:, '年齢層'] = pd.cut(df_filtered['年齢'], bins=age_bins, labels=age_labels, right=False)
    age_distribution = df_filtered.groupby('年齢層')['購入金額'].sum().reset_index()
    
    fig_age = px.bar(
        age_distribution,
        x='年齢層',
        y='購入金額',
        title='年齢層別購入金額分布',
        labels={'年齢層': '年齢層', '購入金額': '購入金額'}
    )
    st.plotly_chart(fig_age, use_container_width=True)

with col2:
    # 性別による購入比率
    gender_distribution = df_filtered.groupby('性別')['購入金額'].sum().reset_index()
    fig_gender = px.pie(
        gender_distribution,
        values='購入金額',
        names='性別',
        title='性別別購入金額比率'
    )
    st.plotly_chart(fig_gender, use_container_width=True)

# 地域別の購入分布
region_distribution = df_filtered.groupby('地域')['購入金額'].sum().reset_index()
fig_region = px.bar(
    region_distribution,
    x='地域',
    y='購入金額',
    title='地域別購入金額分布',
    labels={'地域': '地域', '購入金額': '購入金額'}
)
st.plotly_chart(fig_region, use_container_width=True)

# 4. 商品分析
st.header('4. 商品分析')
col1, col2 = st.columns(2)

with col1:
    # カテゴリー別売上比率
    category_sales = df_filtered.groupby('購入カテゴリー')['購入金額'].sum().reset_index()
    fig_category_pie = px.pie(
        category_sales,
        values='購入金額',
        names='購入カテゴリー',
        title='カテゴリー別売上比率'
    )
    st.plotly_chart(fig_category_pie, use_container_width=True)

with col2:
    # カテゴリー別平均購入金額
    category_avg = df_filtered.groupby('購入カテゴリー')['購入金額'].mean().reset_index()
    fig_category_avg = px.bar(
        category_avg,
        x='購入カテゴリー',
        y='購入金額',
        title='カテゴリー別平均購入金額',
        labels={'購入カテゴリー': 'カテゴリー', '購入金額': '平均購入金額'}
    )
    st.plotly_chart(fig_category_avg, use_container_width=True) 