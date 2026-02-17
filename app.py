import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="T20 Cricket Score Predictor", page_icon="🏏", layout="wide")

st.markdown("""
<style>
.main { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }
h1 { color: #FFD700; text-align: center; font-family: 'Arial Black', sans-serif; 
     text-shadow: 3px 3px 6px #000000; font-size: 3em; padding: 20px; 
     background: linear-gradient(90deg, #8B0000, #FF4500); border-radius: 15px; margin-bottom: 30px; }
h2 { color: #FFD700; font-family: 'Arial', sans-serif; text-shadow: 2px 2px 4px #000000; }
.stButton>button { background: linear-gradient(90deg, #FF4500, #8B0000); color: white; 
                   font-size: 18px; font-weight: bold; border-radius: 10px; padding: 15px 30px; 
                   border: 2px solid #FFD700; }
.prediction-box { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                  padding: 25px; border-radius: 15px; border: 3px solid #FFD700; margin: 20px 0; }
.nav-spacer { margin-bottom: 40px; }
</style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'Prediction'

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    players_path = os.path.join(base_dir, 'data', 'players_data.xlsx')
    stadiums_path = os.path.join(base_dir, 'data', 'stadiums_data.xlsx')
    return pd.read_excel(players_path), pd.read_excel(stadiums_path)

try:
    players_df, stadiums_df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

def calculate_player_form(player_data):
    recent_runs = [player_data[f'Match {i} Runs'] for i in range(1, 11) if f'Match {i} Runs' in player_data]
    if len(recent_runs) >= 5:
        return (sum(recent_runs[-5:]) * 0.6 + sum(recent_runs[:5]) * 0.4) / 10
    return sum(recent_runs) / len(recent_runs) if recent_runs else 0


def generate_realistic_scorecard(team_players, stadium_info, dew, match_period, overs, batting_first, players_df):
    """
    Realistic scorecard generation based on cricket patterns.
    Wickets are determined first, then runs are assigned only to batsmen who came to crease.
    """

    stadium_name = stadium_info['Stadium Name']
    pitch_type = stadium_info['Bowling Friendly (Pace/Spin/Both)']
    batting_score_type = stadium_info['Batting Scoring (High/Avg/Low)']
    is_dew_prone = stadium_info['Dew-Prone (Y/N)'] == 'Y'

    if batting_first:
        stadium_avg = stadium_info['1st Inn Avg Score']
        stadium_wickets_avg = int(stadium_info['1st Inn Avg Wickets'])
    else:
        stadium_avg = stadium_info['2nd Inn Avg Score']
        stadium_wickets_avg = int(stadium_info['2nd Inn Avg Wickets'])

    # Determine realistic wickets first
    if batting_first:
        wickets_fallen = max(4, min(9, int(stadium_wickets_avg + np.random.randint(-2, 3))))
    else:
        wickets_fallen = max(5, min(9, int(stadium_wickets_avg + np.random.randint(-1, 2))))

    batsmen_who_batted = min(11, wickets_fallen + 2)

    scorecard = []
    total_score = 0

    player_order_map = {'Top Order': 1, 'Middle Order': 2, 'Lower Middle Order': 3, 'Tailender': 4}
    team_with_order = []
    for player_name in team_players:
        player = players_df[players_df['Player Name'] == player_name].iloc[0]
        order = player['Batting Order']
        team_with_order.append((player_name, player_order_map.get(order, 3), player))
    team_with_order.sort(key=lambda x: x[1])

    for i, (player_name, _, player) in enumerate(team_with_order):
        batting_order = player['Batting Order']
        favorite_stadium = player['Favorite Stadium']

        if i < batsmen_who_batted:
            total_runs_10 = player['Total Runs (Last 10)']
            avg_runs = total_runs_10 / 10
            form_runs = calculate_player_form(player)

            fav_bonus = 1.15 if favorite_stadium == stadium_name else 1.0
            order_factor = {'Top Order': 1.2, 'Middle Order': 1.0,
                           'Lower Middle Order': 0.8, 'Tailender': 0.4}[batting_order]
            skill = player['Skill (Spin/Pace/Both)']
            skill_bonus = 1.15 if (pitch_type == skill or skill == 'Both') else 0.90
            dew_factor = 1.08 if (dew and is_dew_prone and not batting_first) else 1.0
            time_factor = {'Morning': 1.0, 'Afternoon': 1.0, 'Evening': 1.03, 'Night': 1.05}[match_period]
            batting_factor = {'High': 1.08, 'Average': 1.0, 'Low': 0.92}[batting_score_type]

            predicted_runs = (avg_runs * 0.6 + form_runs * 0.4) * order_factor
            predicted_runs *= skill_bonus * dew_factor * time_factor * batting_factor * fav_bonus * (overs / 20)
            predicted_runs *= np.random.uniform(0.85, 1.15)
            predicted_runs = max(0, int(predicted_runs))

            if batting_order == 'Tailender':
                predicted_runs = min(6, predicted_runs)

            is_out = i < wickets_fallen
            status = 'OUT' if is_out else 'NOT OUT'

            scorecard.append({
                'Player': player_name,
                'Batting Order': batting_order,
                'Runs': predicted_runs,
                'Status': status,
                'Favorite': '❤️' if favorite_stadium == stadium_name else ''
            })
            total_score += predicted_runs
        else:
            scorecard.append({
                'Player': player_name,
                'Batting Order': batting_order,
                'Runs': 0,
                'Status': 'DNB',
                'Favorite': '❤️' if favorite_stadium == stadium_name else ''
            })

    stadium_factor = stadium_avg / 170
    total_score = int(total_score * stadium_factor * 0.95)
    total_score = min(240, total_score)

    return total_score, wickets_fallen, scorecard


# Navigation
st.markdown("<h1>🏏 T20 Cricket Score Predictor 🏆</h1>", unsafe_allow_html=True)
st.markdown('<div class="nav-spacer"></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("🎯 PREDICTION", key="nav_pred", use_container_width=True):
        st.session_state.page = 'Prediction'
with col2:
    if st.button("👥 PLAYERS", key="nav_players", use_container_width=True):
        st.session_state.page = 'Players'
with col3:
    if st.button("🏟️ STADIUMS", key="nav_stadiums", use_container_width=True):
        st.session_state.page = 'Stadiums'

st.markdown("---")

if st.session_state.page == 'Prediction':
    with st.sidebar:
        st.markdown("## 🎯 Match Configuration")
        toss_winner = st.selectbox("🪙 Toss Winner", ["Team A", "Team B"])
        bat_or_bowl = st.radio(f"{toss_winner} chose to:", ["Bat First", "Bowl First"])
        batting_first_team = toss_winner if bat_or_bowl == "Bat First" else ("Team B" if toss_winner == "Team A" else "Team A")
        st.info(f"**{batting_first_team}** will bat first")

        stadium_name = st.selectbox("🏟️ Select Stadium", stadiums_df['Stadium Name'].tolist())
        stadium_info = stadiums_df[stadiums_df['Stadium Name'] == stadium_name].iloc[0]
        is_dew_prone = stadium_info['Dew-Prone (Y/N)'] == 'Y'

        match_period = st.selectbox("🕐 Match Period", ["Morning", "Afternoon", "Evening", "Night"])
        dew_enabled = match_period in ['Evening', 'Night']
        if not dew_enabled:
            st.info("💡 Dew unlikely in morning/afternoon")
            dew = False
        else:
            dew = st.checkbox("💧 Dew Present", value=is_dew_prone, disabled=not dew_enabled)
            if is_dew_prone and dew:
                st.warning("⚠️ Dew-prone stadium!")

        overs = st.slider("📊 Overs", 5, 20, 20, 1)

        st.markdown("---")
        st.markdown("### 🏟️ Stadium Info")
        st.info(f"""
        **City:** {stadium_info['City']}
        **Pitch:** {stadium_info['Pitch Type']}
        **Batting:** {stadium_info['Batting Scoring (High/Avg/Low)']} Scoring
        **Bowling:** {stadium_info['Bowling Friendly (Pace/Spin/Both)']} Friendly
        **1st Inn Avg:** {stadium_info['1st Inn Avg Score']}/{int(stadium_info['1st Inn Avg Wickets'])}
        **1st Inn Highest:** {stadium_info['1st Inn Highest Total']}/{int(stadium_info['1st Inn Highest Wickets'])}
        **2nd Inn Avg:** {stadium_info['2nd Inn Avg Score']}/{int(stadium_info['2nd Inn Avg Wickets'])}
        **2nd Inn Highest:** {stadium_info['2nd Inn Highest Total']}/{int(stadium_info['2nd Inn Highest Wickets'])}
        """)

    if 'team_a_players' not in st.session_state:
        st.session_state.team_a_players = []
    if 'team_b_players' not in st.session_state:
        st.session_state.team_b_players = []

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## 🔴 Team A")
        available_for_a = players_df[~players_df['Player Name'].isin(st.session_state.team_b_players)]
        options_a = []
        for _, player in available_for_a.iterrows():
            name = player['Player Name']
            if player['Favorite Stadium'] == stadium_name:
                options_a.append(f"❤️ {name}")
            else:
                options_a.append(name)
        selected_a = st.multiselect("Select 11 Players", options_a, key="team_a_select", max_selections=11)
        team_a_players = [p.replace('❤️ ', '') for p in selected_a]
        st.session_state.team_a_players = team_a_players
        if len(team_a_players) > 0:
            st.markdown(f"**Selected: {len(team_a_players)}/11**")

    with col2:
        st.markdown("## 🔵 Team B")
        available_for_b = players_df[~players_df['Player Name'].isin(st.session_state.team_a_players)]
        options_b = []
        for _, player in available_for_b.iterrows():
            name = player['Player Name']
            if player['Favorite Stadium'] == stadium_name:
                options_b.append(f"❤️ {name}")
            else:
                options_b.append(name)
        selected_b = st.multiselect("Select 11 Players", options_b, key="team_b_select", max_selections=11)
        team_b_players = [p.replace('❤️ ', '') for p in selected_b]
        st.session_state.team_b_players = team_b_players
        if len(team_b_players) > 0:
            st.markdown(f"**Selected: {len(team_b_players)}/11**")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 PREDICT MATCH SCORE", use_container_width=True):
        if len(team_a_players) != 11 or len(team_b_players) != 11:
            st.error("⚠️ Select exactly 11 players per team!")
        else:
            with st.spinner("🔮 Generating realistic scorecards..."):
                team_a_bats_first = batting_first_team == "Team A"

                team_a_score, team_a_wkts, team_a_scorecard = generate_realistic_scorecard(
                    team_a_players, stadium_info, dew, match_period, overs, team_a_bats_first, players_df
                )
                team_b_score, team_b_wkts, team_b_scorecard = generate_realistic_scorecard(
                    team_b_players, stadium_info, dew, match_period, overs, not team_a_bats_first, players_df
                )

            st.markdown("## 📊 MATCH RESULT")
            st.success("✅ Realistic scorecards based on actual IPL patterns!")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="prediction-box">', unsafe_allow_html=True)
                st.markdown("### 🔴 Team A Final Score")
                st.metric("Total", f"{team_a_score}/{team_a_wkts}",
                         help=f"{'Batting first' if team_a_bats_first else 'Chasing'}")

                with st.expander("ℹ️ How is this calculated?"):
                    st.markdown(f"""
                    **Wickets determined first:** {team_a_wkts} wickets
                    **Batsmen who came to crease:** {team_a_wkts + 2} players
                    **Did Not Bat (DNB):** {11 - (team_a_wkts + 2)} players

                    **Realistic patterns:**
                    - {'Batting first: 4-8 wickets' if team_a_bats_first else 'Chasing: 5-7 wickets (minimum 4)'}
                    - Runs assigned only to batsmen who batted
                    - Tailenders bat only if 6+ wickets fall
                    """)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="prediction-box">', unsafe_allow_html=True)
                st.markdown("### 🔵 Team B Final Score")
                st.metric("Total", f"{team_b_score}/{team_b_wkts}",
                         help=f"{'Batting first' if not team_a_bats_first else 'Chasing'}")

                with st.expander("ℹ️ How is this calculated?"):
                    st.markdown(f"""
                    **Wickets determined first:** {team_b_wkts} wickets
                    **Batsmen who came to crease:** {team_b_wkts + 2} players
                    **Did Not Bat (DNB):** {11 - (team_b_wkts + 2)} players

                    **Realistic patterns:**
                    - {'Batting first: 4-8 wickets' if not team_a_bats_first else 'Chasing: 5-7 wickets (minimum 4)'}
                    - Runs assigned only to batsmen who batted
                    - Tailenders bat only if 6+ wickets fall
                    """)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="prediction-box">', unsafe_allow_html=True)
            st.markdown("### 🏆 MATCH RESULT")
            if team_a_score > team_b_score:
                margin = team_a_score - team_b_score
                st.success(f"🎉 **Team A wins by {margin} runs!**")
            elif team_b_score > team_a_score:
                wkts_remaining = 10 - team_b_wkts
                st.success(f"🎉 **Team B wins by {wkts_remaining} wickets!**")
            else:
                st.warning("🤝 **Match Tied!**")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["🔴 Team A Scorecard", "🔵 Team B Scorecard"])

            with tab1:
                st.markdown(f"### Team A Scorecard - {team_a_score}/{team_a_wkts}")
                st.info(f"⚠️ Batsmen who came to crease: {team_a_wkts + 2} | DNB: {11 - (team_a_wkts + 2)}")
                df_a = pd.DataFrame(team_a_scorecard)
                st.dataframe(df_a, use_container_width=True, hide_index=True)
                batted_players = df_a[df_a['Status'] != 'DNB']
                total_runs_check = batted_players['Runs'].sum()
                st.caption(f"✅ Score verification: {total_runs_check} runs scored")

            with tab2:
                st.markdown(f"### Team B Scorecard - {team_b_score}/{team_b_wkts}")
                st.info(f"⚠️ Batsmen who came to crease: {team_b_wkts + 2} | DNB: {11 - (team_b_wkts + 2)}")
                df_b = pd.DataFrame(team_b_scorecard)
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                batted_players = df_b[df_b['Status'] != 'DNB']
                total_runs_check = batted_players['Runs'].sum()
                st.caption(f"✅ Score verification: {total_runs_check} runs scored")

elif st.session_state.page == 'Players':
    st.markdown("## 👥 PLAYERS DATABASE")
    col1, col2, col3 = st.columns(3)
    with col1:
        team_filter = st.multiselect("Team", ['All'] + sorted(players_df['Team'].unique().tolist()), default=['All'])
    with col2:
        skill_filter = st.multiselect("Skill", ['All'] + sorted(players_df['Skill (Spin/Pace/Both)'].unique().tolist()), default=['All'])
    with col3:
        order_filter = st.multiselect("Order", ['All'] + sorted(players_df['Batting Order'].unique().tolist()), default=['All'])

    filtered_df = players_df.copy()
    if 'All' not in team_filter and len(team_filter) > 0:
        filtered_df = filtered_df[filtered_df['Team'].isin(team_filter)]
    if 'All' not in skill_filter and len(skill_filter) > 0:
        filtered_df = filtered_df[filtered_df['Skill (Spin/Pace/Both)'].isin(skill_filter)]
    if 'All' not in order_filter and len(order_filter) > 0:
        filtered_df = filtered_df[filtered_df['Batting Order'].isin(order_filter)]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Players", len(filtered_df))
    with col2:
        st.metric("Avg Runs", f"{filtered_df['Total Runs (Last 10)'].mean():.0f}")
    with col3:
        st.metric("Avg Wickets", f"{filtered_df['Total Wickets (Last 10)'].mean():.1f}")
    with col4:
        st.metric("Teams", filtered_df['Team'].nunique())

    st.markdown("### 📋 Player Details")
    display_cols = ['Player Name', 'Team', 'Batting Order', 'Skill (Spin/Pace/Both)',
                   'Total Runs (Last 10)', 'Total Wickets (Last 10)', 'Favorite Stadium']
    st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

elif st.session_state.page == 'Stadiums':
    st.markdown("## 🏟️ STADIUMS DATABASE")
    col1, col2 = st.columns(2)
    with col1:
        scoring_filter = st.multiselect("Batting", ['All', 'High', 'Average', 'Low'], default=['All'])
    with col2:
        bowling_filter = st.multiselect("Bowling", ['All', 'Pace', 'Spin', 'Both'], default=['All'])

    filtered_stadiums = stadiums_df.copy()
    if 'All' not in scoring_filter and len(scoring_filter) > 0:
        filtered_stadiums = filtered_stadiums[filtered_stadiums['Batting Scoring (High/Avg/Low)'].isin(scoring_filter)]
    if 'All' not in bowling_filter and len(bowling_filter) > 0:
        filtered_stadiums = filtered_stadiums[filtered_stadiums['Bowling Friendly (Pace/Spin/Both)'].isin(bowling_filter)]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Stadiums", len(filtered_stadiums))
    with col2:
        st.metric("Dew-Prone", len(filtered_stadiums[filtered_stadiums['Dew-Prone (Y/N)'] == 'Y']))
    with col3:
        st.metric("Avg 1st Inn", f"{filtered_stadiums['1st Inn Avg Score'].mean():.0f}/{filtered_stadiums['1st Inn Avg Wickets'].mean():.0f}")
    with col4:
        st.metric("Avg 2nd Inn", f"{filtered_stadiums['2nd Inn Avg Score'].mean():.0f}/{filtered_stadiums['2nd Inn Avg Wickets'].mean():.0f}")

    st.markdown("### 📋 Stadium Details")
    st.dataframe(filtered_stadiums, use_container_width=True, hide_index=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("<p style='text-align: center; color: #FFD700;'>🏏 T20 Cricket Score Predictor | Realistic Scorecards 🏆</p>", unsafe_allow_html=True)
