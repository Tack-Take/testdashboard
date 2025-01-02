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
tab1, tab2 = st.tabs(["基本分析", "クロス分析"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # 年齢層別の購入分布
        age_bins = [0, 20, 30, 40, 50, 60, 70, 100]
        age_labels = ['20歳未満', '20-30歳', '31-40歳', '41-50歳', '51-60歳', '61-70歳', '71歳以上']
        df_filtered.loc[:, '年齢層'] = pd.cut(df_filtered['年齢'], bins=age_bins, labels=age_labels, right=False)
        age_distribution = df_filtered.groupby('年齢層')['購入金額'].agg(['sum', 'count']).reset_index()
        
        fig_age = px.bar(
            age_distribution,
            x='年齢層',
            y='sum',
            title='年齢層別購入金額分布',
            labels={'sum': '購入金額', '年齢層': ''},
            text=age_distribution['count'].apply(lambda x: f'{x}件')
        )
        fig_age.update_traces(textposition='outside')
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
    region_distribution = df_filtered.groupby('地域')['購入金額'].agg(['sum', 'count']).reset_index()
    fig_region = px.bar(
        region_distribution,
        x='地域',
        y='sum',
        title='地域別購入金額分布',
        labels={'sum': '購入金額', '地域': ''},
        text=region_distribution['count'].apply(lambda x: f'{x}件')
    )
    fig_region.update_traces(textposition='outside')
    st.plotly_chart(fig_region, use_container_width=True)

with tab2:
    # 年齢層×性別のクロス分析
    st.subheader("年齢層×性別のクロス分析")
    age_gender_cross = pd.pivot_table(
        df_filtered,
        values='購入金額',
        index='年齢層',
        columns='性別',
        aggfunc='sum',
        fill_value=0
    )
    
    fig_age_gender = px.bar(
        age_gender_cross,
        barmode='group',
        title='年齢層×性別の購入金額分布',
        labels={'value': '購入金額', 'index': '年齢層'}
    )
    st.plotly_chart(fig_age_gender, use_container_width=True)

    # 地域×カテゴリーのクロス分析
    st.subheader("地域×カテゴリーのクロス分析")
    region_category_cross = pd.pivot_table(
        df_filtered,
        values='購入金額',
        index='地域',
        columns='購入カテゴリー',
        aggfunc='sum',
        fill_value=0
    )
    
    fig_region_category = px.bar(
        region_category_cross,
        barmode='group',
        title='地域×カテゴリー別の購入金額分布',
        labels={'value': '購入金額', 'index': '地域'}
    )
    st.plotly_chart(fig_region_category, use_container_width=True)

    # 購入金額帯別の顧客分布
    st.subheader("購入金額帯別の顧客分布")
    amount_bins = [0, 5000, 10000, 30000, 50000, 100000]
    amount_labels = ['5,000円未満', '5,000-10,000円', '10,000-30,000円', '30,000-50,000円', '50,000円以上']
    df_filtered.loc[:, '購入金額帯'] = pd.cut(df_filtered['購入金額'], bins=amount_bins, labels=amount_labels, right=False)
    
    # 購入金額帯別の集計
    amount_range_dist = df_filtered.groupby('購入金額帯').agg({
        '顧客ID': 'count',
        '購入金額': 'sum'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 購入金額帯別の顧客数
        fig_amount_range_count = px.bar(
            amount_range_dist,
            x='購入金額帯',
            y='顧客ID',
            title='購入金額帯別の顧客数',
            labels={'顧客ID': '顧客数', '購入金額帯': ''}
        )
        st.plotly_chart(fig_amount_range_count, use_container_width=True)
    
    with col2:
        # 購入金額帯別の売上金額
        fig_amount_range_sum = px.bar(
            amount_range_dist,
            x='購入金額帯',
            y='購入金額',
            title='購入金額帯別の売上金額',
            labels={'購入金額': '売上金額', '購入金額帯': ''}
        )
        st.plotly_chart(fig_amount_range_sum, use_container_width=True)

# 4. 商品分析
st.header('4. 商品分析')
tab1, tab2 = st.tabs(["基本分析", "詳細分析"])

with tab1:
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

with tab2:
    # カテゴリー別注文件数推移
    st.subheader("カテゴリー別注文件数推移")
    category_time_series = df_filtered.groupby([
        pd.Grouper(key='購入日', freq='M'),
        '購入カテゴリー'
    ]).size().reset_index(name='注文件数')
    
    fig_category_trend = px.line(
        category_time_series,
        x='購入日',
        y='注文件数',
        color='購入カテゴリー',
        title='カテゴリー別月次注文件数推移',
        labels={'購入日': '年月', '注文件数': '注文件数'}
    )
    st.plotly_chart(fig_category_trend, use_container_width=True)

    # 価格帯分析
    st.subheader("価格帯分析")
    col1, col2 = st.columns(2)

    with col1:
        # カテゴリー別の価格帯分布（箱ひげ図）
        fig_price_box = px.box(
            df_filtered,
            x='購入カテゴリー',
            y='購入金額',
            title='カテゴリー別価格分布',
            labels={'購入カテゴリー': 'カテゴリー', '購入金額': '購入金額'}
        )
        st.plotly_chart(fig_price_box, use_container_width=True)

    with col2:
        # 高額商品の売上貢献度分析
        df_filtered_sorted = df_filtered.sort_values('購入金額', ascending=False)
        cumsum_sales = df_filtered_sorted['購入金額'].cumsum()
        total_sales = df_filtered_sorted['購入金額'].sum()
        df_filtered_sorted['累計売上比率'] = (cumsum_sales / total_sales * 100)
        
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=list(range(len(df_filtered_sorted))),
            y=df_filtered_sorted['購入金額'],
            name='購入金額'
        ))
        fig_pareto.add_trace(go.Scatter(
            x=list(range(len(df_filtered_sorted))),
            y=df_filtered_sorted['累計売上比率'],
            name='累計売上比率',
            yaxis='y2',
            line=dict(color='red')
        ))
        
        fig_pareto.update_layout(
            title='パレート分析（高額商品の売上貢献度）',
            yaxis=dict(title='購入金額'),
            yaxis2=dict(
                title='累計売上比率 (%)',
                overlaying='y',
                side='right',
                range=[0, 100]
            ),
            showlegend=True
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

    # 価格帯別の分布
    price_bins = [0, 5000, 10000, 30000, 50000, 100000]
    price_labels = ['5,000円未満', '5,000-10,000円', '10,000-30,000円', '30,000-50,000円', '50,000円以上']
    df_filtered.loc[:, '価格帯'] = pd.cut(df_filtered['購入金額'], bins=price_bins, labels=price_labels, right=False)
    
    price_range_dist = df_filtered.groupby(['価格帯', '購入カテゴリー']).size().reset_index(name='件数')
    fig_price_range = px.bar(
        price_range_dist,
        x='価格帯',
        y='件数',
        color='購入カテゴリー',
        title='価格帯×カテゴリー別の販売数分布',
        labels={'価格帯': '', '件数': '販売数'}
    )
    st.plotly_chart(fig_price_range, use_container_width=True)

# 5. 決済分析
st.header('5. 決済分析')
tab1, tab2 = st.tabs(["基本分析", "クロス分析"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        # 決済方法別の利用比率
        payment_distribution = df_filtered.groupby('支払方法')['購入金額'].agg(['sum', 'count']).reset_index()
        fig_payment_pie = px.pie(
            payment_distribution,
            values='sum',
            names='支払方法',
            title='決済方法別売上比率',
            hover_data=['count']
        )
        st.plotly_chart(fig_payment_pie, use_container_width=True)

    with col2:
        # 決済方法別の平均購入金額
        payment_avg = df_filtered.groupby('支払方法')['購入金額'].mean().reset_index()
        fig_payment_avg = px.bar(
            payment_avg,
            x='支払方法',
            y='購入金額',
            title='決済方法別平均購入金額',
            labels={'支払方法': '', '購入金額': '平均購入金額'}
        )
        st.plotly_chart(fig_payment_avg, use_container_width=True)

with tab2:
    # 年齢層別の決済方法選択傾向
    st.subheader("年齢層別の決済方法選択傾向")
    age_payment_cross = pd.pivot_table(
        df_filtered,
        values='購入金額',
        index='年齢層',
        columns='支払方法',
        aggfunc='count',
        fill_value=0
    )
    
    # 割合に変換
    age_payment_pct = age_payment_cross.div(age_payment_cross.sum(axis=1), axis=0) * 100
    
    fig_age_payment = px.bar(
        age_payment_pct,
        barmode='stack',
        title='年齢層別の決済方法利用比率',
        labels={'value': '利用比率 (%)', 'index': '年齢層'}
    )
    st.plotly_chart(fig_age_payment, use_container_width=True)

    # カテゴリー別の決済方法選択傾向
    st.subheader("カテゴリー別の決済方法選択傾向")
    category_payment_cross = pd.pivot_table(
        df_filtered,
        values='購入金額',
        index='購入カテゴリー',
        columns='支払方法',
        aggfunc='count',
        fill_value=0
    )
    
    # 割合に変換
    category_payment_pct = category_payment_cross.div(category_payment_cross.sum(axis=1), axis=0) * 100
    
    fig_category_payment = px.bar(
        category_payment_pct,
        barmode='stack',
        title='カテゴリー別の決済方法利用比率',
        labels={'value': '利用比率 (%)', 'index': 'カテゴリー'}
    )
    st.plotly_chart(fig_category_payment, use_container_width=True)

    # 購入金額帯別の決済方法分布
    st.subheader("購入金額帯別の決済方法分布")
    amount_payment_cross = pd.pivot_table(
        df_filtered,
        values='購入金額',
        index='購入金額帯',
        columns='支払方法',
        aggfunc='count',
        fill_value=0
    )
    
    # 割合に変換
    amount_payment_pct = amount_payment_cross.div(amount_payment_cross.sum(axis=1), axis=0) * 100
    
    fig_amount_payment = px.bar(
        amount_payment_pct,
        barmode='stack',
        title='購入金額帯別の決済方法利用比率',
        labels={'value': '利用比率 (%)', 'index': '購入金額帯'}
    )
    st.plotly_chart(fig_amount_payment, use_container_width=True)

# 6. レポート出力
st.header('6. レポート出力')
tab1, tab2 = st.tabs(["データエクスポート", "PDFレポート"])

with tab1:
    st.subheader("データのエクスポート")
    
    # エクスポート対象の選択
    export_options = {
        '全データ': df_filtered,
        '売上サマリー（日次）': df_filtered.groupby('購入日')['購入金額'].agg(['sum', 'count', 'mean']).reset_index(),
        '売上サマリー（月次）': df_filtered.groupby(df_filtered['購入日'].dt.strftime('%Y-%m'))['購入金額'].agg(['sum', 'count', 'mean']).reset_index(),
        'カテゴリー別集計': df_filtered.groupby('購入カテゴリー')['購入金額'].agg(['sum', 'count', 'mean']).reset_index(),
        '地域別集計': df_filtered.groupby('地域')['購入金額'].agg(['sum', 'count', 'mean']).reset_index()
    }
    
    export_selection = st.selectbox(
        'エクスポートするデータを選択してください：',
        list(export_options.keys())
    )
    
    # CSVダウンロードボタン
    if st.button('CSVファイルをダウンロード'):
        csv = export_options[export_selection].to_csv(index=False)
        st.download_button(
            label="CSVファイルのダウンロードを開始",
            data=csv,
            file_name=f'{export_selection}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv'
        )

with tab2:
    st.subheader("PDFレポートの生成")
    
    # レポート設定
    st.write("レポートに含める内容を選択してください：")
    
    report_options = {
        '売上概要': st.checkbox('売上概要', value=True),
        '時系列分析': st.checkbox('時系列分析', value=True),
        '顧客分析': st.checkbox('顧客分析'),
        '商品分析': st.checkbox('商品分析'),
        '決済分析': st.checkbox('決済分析')
    }
    
    # PDFレポートの生成ボタン
    if st.button('PDFレポートを生成'):
        # ここでは実際のPDF生成は行わず、機能の説明を表示
        st.info('この機能は開発中です。完成時には以下の機能が利用可能になります：')
        st.markdown("""
        - 選択した分析内容を含むPDFレポートの生成
        - グラフや表の自動レイアウト
        - 分析結果の自動コメント生成
        - ブランドテンプレートの適用
        """)

# 7. アラート設定
st.header('7. アラート設定')

# アラート条件の設定
st.subheader("アラート条件の設定")

col1, col2 = st.columns(2)

with col1:
    # 売上アラート
    st.write("売上アラート")
    sales_threshold = st.number_input(
        "1日の売上がこの金額を下回った場合に通知",
        min_value=0,
        value=100000,
        step=10000
    )
    
    # 異常検知の感度
    st.write("異常検知の感度")
    sensitivity = st.slider(
        "異常検知の感度を調整",
        min_value=1,
        max_value=5,
        value=3,
        help="1: 低感度（重要な異常のみ） ～ 5: 高感度（軽微な異常も検知）"
    )

with col2:
    # カテゴリーアラート
    st.write("カテゴリー別アラート")
    category_threshold = st.number_input(
        "カテゴリー別の売上が前月比でこの割合を下回った場合に通知",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
        help="例：20を入力すると、前月比-20%以上の下落で通知"
    )

# アラート通知設定
st.subheader("通知設定")
notification_methods = {
    'メール通知': st.checkbox('メール通知を有効化'),
    'LINE通知': st.checkbox('LINE通知を有効化'),
    'Slack通知': st.checkbox('Slack通知を有効化')
}

if st.button('設定を保存'):
    st.success('アラート設定を保存しました（デモ表示）')
    
# アラート履歴の表示（デモデータ）
st.subheader("最近のアラート履歴")
alert_history = pd.DataFrame({
    '日時': ['2024-01-20 10:30', '2024-01-19 15:45', '2024-01-18 09:15'],
    'タイプ': ['売上低下', 'カテゴリー売上異常', '異常値検知'],
    '内容': [
        '本日の売上が設定された閾値を下回りました',
        '衣類カテゴリーの売上が前月比-25%',
        '通常の2倍を超える注文数を検知'
    ]
})
st.dataframe(alert_history, hide_index=True)

# 8. 予測分析
st.header('8. 予測分析')
tab1, tab2 = st.tabs(["売上予測", "トレンド分析"])

with tab1:
    st.subheader("売上予測")
    
    # 予測期間の選択
    forecast_period = st.slider(
        "予測期間（日数）を選択",
        min_value=7,
        max_value=90,
        value=30,
        step=7
    )
    
    # 予測モデルの選択
    forecast_model = st.selectbox(
        "予測モデルを選択",
        ["シンプル移動平均", "指数平滑法", "SARIMA", "機械学習モデル"]
    )
    
    if st.button('予測を実行'):
        # ここでは簡単な移動平均による予測をデモ表示
        last_date = df_filtered['購入日'].max()
        future_dates = pd.date_range(start=last_date, periods=forecast_period + 1)[1:]
        
        # 過去30日の移動平均を計算
        avg_daily_sales = df_filtered.groupby('購入日')['購入金額'].sum().rolling(window=30).mean().iloc[-1]
        
        # 予測データの作成（デモ用）
        forecast_data = pd.DataFrame({
            '日付': future_dates,
            '予測売上': [avg_daily_sales * (1 + np.random.normal(0, 0.1)) for _ in range(len(future_dates))]
        })
        
        # 予測結果の表示
        fig_forecast = px.line(
            forecast_data,
            x='日付',
            y='予測売上',
            title=f'今後{forecast_period}日間の売上予測'
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
        
        # 予測信頼区間の説明
        st.info('青い線は予測値を、灰色の帯は予測の信頼区間を示しています（デモ表示）')

with tab2:
    st.subheader("トレンド分析")
    
    # トレンド分析の対象選択
    trend_target = st.selectbox(
        "分析対象を選択",
        ["売上金額", "注文件数", "平均購入金額"]
    )
    
    # トレンドの種類選択
    trend_type = st.selectbox(
        "トレンドの種類を選択",
        ["長期トレンド", "季節性", "周期性"]
    )
    
    if st.button('トレンド分析を実行'):
        # デモ用のトレンド分析結果表示
        st.write("トレンド分析結果（デモ表示）")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # トレンド要素の分解（デモ）
            st.write("トレンド要素の分解")
            st.image("https://raw.githubusercontent.com/streamlit/demo-uber-nyc-pickups/main/data/decomposition.png", 
                    caption="※これはデモ画像です")
        
        with col2:
            # 主要な指標
            st.write("主要な指標")
            st.metric(label="トレンドの方向", value="上昇傾向", delta="+5.2%")
            st.metric(label="季節性の強さ", value="中程度", delta="0.3")
            st.metric(label="予測精度", value="85%", delta="+2.1%")

# ... rest of the existing code ... 