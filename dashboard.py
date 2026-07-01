"""
LoL Analytics Dashboard

Дашборд для анализа:
- распределения LP игроков
- длительности матчей
- топ чемпионов по винрейту
- зависимости kills/deaths

Фильтры:
- регион (EUW/NA)
- лига (Master/Grandmaster/Challenger)
"""

# Импорт библиотек
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Загрузка подготовленных данных
players = pd.read_csv("players_data.csv")
matches = pd.read_csv("matches_data.csv")
participants_df = pd.read_csv("participants.csv")

# Удаление возможных дублей игроков в рамках одного матча
player_base = participants_df.drop_duplicates(subset=["match_id", "puuid"])

# Фильтрация таблиц игроков и матчей по региону и лиге
def filter_data(players, matches, region="All", league="All"):
    # Создаем копии
    players_f = players.copy()
    matches_f = matches.copy()

    # Фильтр по региону
    if region != "All":
        players_f = players_f[players_f["region"] == region]
        matches_f = matches_f[matches_f["region"] == region]

    # Фильтр по лиге
    if league != "All":
        players_f = players_f[players_f["league"] == league]
        matches_f = matches_f[matches_f["league"] == league]

    return players_f, matches_f

# Фильтрация таблицы участников матчей
def filter_player_base(player_base, region="All", league="All"):
    df = player_base.copy()

    if region != "All":
        df = df[df["region"] == region]

    if league != "All":
        df = df[df["league"] == league]

    return df

# Расчет агрегированной статистики по чемпионам
def build_champion_stats(df):
    champions = df.groupby("champion").agg(
        matches=("champion", "size"),
        wins=("win", "sum"),
        kills=("kills", "mean"),
        deaths=("deaths", "mean"),
        assists=("assists", "mean")
    ).reset_index()

    champions["winrate"] = champions["wins"] / champions["matches"]

    return champions

# Создание приложения Dash
app = dash.Dash(__name__)

# Описание интерфейса дашборда
app.layout = html.Div([

    # Заголовок
    html.H1("LoL Analytics Dashboard"),

     # Cписок выбора региона
    dcc.Dropdown(
        id="region",
        options=[
            {"label": "EUW", "value": "euw"},
            {"label": "NA", "value": "na"},
            {"label": "All", "value": "All"}
        ],
        value="euw"
    ),

    # Cписок выбора лиги
    dcc.Dropdown(
        id="league",
        options=[
            {"label": "Master", "value": "master"},
            {"label": "Grandmaster", "value": "grandmaster"},
            {"label": "Challenger", "value": "challenger"},
            {"label": "All", "value": "All"}
        ],
        value="master"
    ),

    # Графики
    dcc.Graph(id="top-champions"),
    dcc.Graph(id="lp-dist"),
    dcc.Graph(id="duration"),
    dcc.Graph(id="scatter")
])

# Обновление всех графиков при изменении фильтров
@app.callback(
    Output("top-champions", "figure"),
    Output("lp-dist", "figure"),
    Output("duration", "figure"),
    Output("scatter", "figure"),
    Input("region", "value"),
    Input("league", "value")
)
def update(region, league):

    # Фильтрация данных игроков и матчей
    players_f, matches_f = filter_data(players, matches, region, league)

    # Фильтрация данных участников матчей
    player_base_f = filter_player_base(player_base, region, league)

    # Построение статистики по чемпионам
    champions_f = build_champion_stats(player_base_f)

    # Построение статистики по чемпионам
    BI_LAYOUT = dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            linecolor="black",
            tickfont=dict(color="black")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            linecolor="black",
            tickfont=dict(color="black")
         )
    )


    # 1. Топ чемпионов по винрейту
    top = champions_f.sort_values("winrate", ascending=False).head(15)
    
    fig1 = px.bar(
        top,
        x="champion",
        y="winrate",
        title="Top Champions by Winrate",
        color_discrete_sequence=["#4DA3FF"]
    )

    fig1.update_traces(
        marker=dict(
            line=dict(color="black", width=1)
        )
    )

    fig1.update_layout(**BI_LAYOUT)

    # 2. Распределение League Points (LP)
    lp = players_f[players_f["leaguePoints"].notna()]

    fig2 = px.histogram(
        lp,
        x="leaguePoints",
        nbins=30,
        title="LP Distribution"
    )

    fig2.update_traces(
        marker=dict(
            color="#4DA3FF",
            line=dict(color="black", width=0.8)
        )
    )

    fig2.update_layout(**BI_LAYOUT)

    # 3. Распределение длительности матчей
    matches_f["game_duration_min"] = matches_f["game_duration"] / 60
    matches_f["game_duration_min"] = matches_f["game_duration_min"].round(1)
    
    fig3 = px.box(
        matches_f,
        y="game_duration",
        title="Match Duration (minutes)",
        color_discrete_sequence=["#4DA3FF"]
    )

    fig3.update_traces(
        marker=dict(
            color="#4DA3FF",
            line=dict(color="black", width=1)
        )
    )
    
    fig3.update_layout(**BI_LAYOUT)

    # 4. Зависимость среднего количества убийств и смертей чемпионов
    fig4 = px.scatter(
        champions_f,
        x="deaths",
        y="kills",
        size="matches",
        color="winrate",
        hover_name="champion",
        title="Kills vs Deaths by Champion",
        color_continuous_scale="Blues"
    )

    fig4.update_traces(
        marker=dict(
            line=dict(color="black", width=1)
        )
    )

    fig4.update_layout(**BI_LAYOUT)

    return fig1, fig2, fig3, fig4

# Запуск приложения в режиме разработки
if __name__ == "__main__":
    app.run(debug=True)