"""
房源数据分析页面
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import db_manager

st.set_page_config(page_title="数据分析", page_icon="📊", layout="wide")

def main():
    st.title("📊 房源数据分析")

    try:
        # 获取所有房源数据进行分析
        all_houses = db_manager.get_houses(limit=10000)

        if len(all_houses) == 0:
            st.warning("没有可分析的数据")
            return

        # 数据预处理
        all_houses['price_numeric'] = pd.to_numeric(all_houses['price'], errors='coerce')
        all_houses['area_numeric'] = pd.to_numeric(all_houses['area'], errors='coerce')

        # 去除异常值
        all_houses = all_houses[
            (all_houses['price_numeric'] > 0) &
            (all_houses['price_numeric'] < 100000) &
            (all_houses['area_numeric'] > 0) &
            (all_houses['area_numeric'] < 1000)
        ]

        # 基础统计信息
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("总房源数", len(all_houses))

        with col2:
            avg_price = all_houses['price_numeric'].mean()
            st.metric("平均租金", f"¥{avg_price:.0f}/月")

        with col3:
            avg_area = all_houses['area_numeric'].mean()
            st.metric("平均面积", f"{avg_area:.1f}㎡")

        with col4:
            avg_unit_price = (all_houses['price_numeric'] / all_houses['area_numeric']).mean()
            st.metric("平均单价", f"¥{avg_unit_price:.1f}/㎡")

        st.divider()

        # 图表分析
        col1, col2 = st.columns(2)

        with col1:
            # 价格分布
            st.subheader("💰 租金分布")
            fig_price = px.histogram(
                all_houses,
                x='price_numeric',
                nbins=30,
                title="租金分布直方图",
                labels={'price_numeric': '租金(元/月)', 'count': '房源数量'}
            )
            st.plotly_chart(fig_price, use_container_width=True)

        with col2:
            # 面积分布
            st.subheader("📐 面积分布")
            fig_area = px.histogram(
                all_houses,
                x='area_numeric',
                nbins=30,
                title="面积分布直方图",
                labels={'area_numeric': '面积(㎡)', 'count': '房源数量'}
            )
            st.plotly_chart(fig_area, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            # 区域分布
            st.subheader("🏙️ 区域房源分布")
            region_counts = all_houses['region'].value_counts().head(10)
            fig_region = px.bar(
                x=region_counts.index,
                y=region_counts.values,
                title="各区域房源数量TOP10",
                labels={'x': '区域', 'y': '房源数量'}
            )
            st.plotly_chart(fig_region, use_container_width=True)

        with col2:
            # 租赁类型分布
            st.subheader("🏠 租赁类型分布")
            rent_type_counts = all_houses['rent_type'].value_counts()
            fig_rent = px.pie(
                values=rent_type_counts.values,
                names=rent_type_counts.index,
                title="租赁类型占比"
            )
            st.plotly_chart(fig_rent, use_container_width=True)

        # 房型分析
        st.subheader("🏡 房型与价格关系")
        room_price = all_houses.groupby('rooms')['price_numeric'].agg(['mean', 'count']).reset_index()
        room_price = room_price[room_price['count'] >= 10]  # 只显示房源数量>=10的房型

        fig_room_price = px.bar(
            room_price,
            x='rooms',
            y='mean',
            title="不同房型的平均租金",
            labels={'rooms': '房型', 'mean': '平均租金(元/月)'}
        )
        st.plotly_chart(fig_room_price, use_container_width=True)

        # 价格与面积散点图
        st.subheader("💹 租金与面积关系")
        sample_data = all_houses.sample(min(1000, len(all_houses)))  # 随机采样1000条数据

        fig_scatter = px.scatter(
            sample_data,
            x='area_numeric',
            y='price_numeric',
            color='region',
            title="租金与面积关系散点图",
            labels={'area_numeric': '面积(㎡)', 'price_numeric': '租金(元/月)'},
            hover_data=['title', 'rooms']
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        # 热门区域详细分析
        st.subheader("🔥 热门区域分析")
        top_regions = all_houses['region'].value_counts().head(5).index

        for region in top_regions:
            region_data = all_houses[all_houses['region'] == region]

            with st.expander(f"📍 {region} (共{len(region_data)}套房源)"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("平均租金", f"¥{region_data['price_numeric'].mean():.0f}/月")

                with col2:
                    st.metric("平均面积", f"{region_data['area_numeric'].mean():.1f}㎡")

                with col3:
                    avg_unit = (region_data['price_numeric'] / region_data['area_numeric']).mean()
                    st.metric("平均单价", f"¥{avg_unit:.1f}/㎡")

                # 该区域的房型分布
                room_dist = region_data['rooms'].value_counts()
                fig_room_dist = px.pie(
                    values=room_dist.values,
                    names=room_dist.index,
                    title=f"{region}房型分布"
                )
                st.plotly_chart(fig_room_dist, use_container_width=True)

    except Exception as e:
        st.error(f"数据分析时出错: {str(e)}")

if __name__ == "__main__":
    main()