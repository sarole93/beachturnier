from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import ( StringProperty, BooleanProperty, ObjectProperty )
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.utils import platform
from kivy.core.window import Window

import pandas as pd
import os
import time
import re

# Define default data
filename_players_init = '_spieler.csv' # file ending to retrieve and store player data
filename_tournament_init = '_turnier.csv' # file ending to retrieve and store tournament data
default_name_init = 'default' # default file and tournament name
num_tries_init = 200 # number of attempts to find new pairings
# formulae to determine points and ranking
points_init = lambda wins, draws: wins*3 + draws
ranking_init = lambda wins, draws, points_won, points_lost: wins*3 + draws + 0.5 + (points_won-points_lost)/1000

class NumInputPat(TextInput):
    pat = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = re.sub(pat, '', substring)
        return super(NumInputPat, self).insert_text(s, from_undo=from_undo)
class TextInputPat(TextInput):
    pat = re.compile('[^A-Za-z0-9 _,.]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = re.sub(pat, '', substring)
        return super(TextInputPat, self).insert_text(s, from_undo=from_undo)

class MainScreen(Widget):    
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        app = App.get_running_app()

    def show_options(self):
        content = Options(close=self.dismiss_popup)
        self._popup = Popup(title='Beachturnier Mixed', content=content,
                            size_hint=(1, 1))
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

class Navigation(TabbedPanel):
    def __init__(self, **kwargs):
        super(Navigation, self).__init__(**kwargs)
        app = App.get_running_app()

class Options(GridLayout):    
    close = ObjectProperty(None)
    def __init__(self, close, **kwargs):
        super(Options, self).__init__(**kwargs)
        app = App.get_running_app()
        self.reload_ = False
        self.delete_ = False
        self.close = close
    
    def reload(self, app):
        self.reload_ = True
        app.apply_changes = False
        app.change_message = 'Neu laden?'
        self.delete_ = False
        
    def delete(self, app):
        self.delete_ = True
        app.apply_changes = False
        app.change_message = 'Löschen?'
        self.reload_ = False
    
    def update(self, app):
        app.update_data(self.ids.new_filename.text)
        app.save_status = False
        app.apply_changes = True
        app.change_message = ''
    
    def apply(self, app):
        app.file_players = self.ids.new_filename.text + app.file_players_ending
        app.file_tournament = self.ids.new_filename.text + app.file_tournament_ending
        if self.delete_ == True:
            app.delete()
        if self.reload_ == True:
            app.read_data()
        app.apply_changes = True
        app.change_message = ''
        app.save_status = True
        self.reload_ = False
        self.delete_ = False
            
    def cancel(self, app):
        self.delete_ = False
        self.reload_ = False
        app.apply_changes = True
        app.change_message = ''

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_import(self):
        content = LoadDialog(import_data=self.import_data, cancel=self.dismiss_popup)
        self._popup = Popup(title='Savefile importieren', content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_export(self):
        content = SaveDialog(export_data=self.export_data, cancel=self.dismiss_popup)
        self._popup = Popup(title='Savefile exportieren', content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def import_data(self, app, path, filename):
        try:
            app.import_data(path, filename[0])
        except PermissionError:
            app.print_error('general', 'Kann File nicht öffnen (fehlende Rechte).')
        app.save_data()
        app.print_saves()
        
        self.dismiss_popup()

    def export_data(self, app, path, filename):
        try:
            app.export_data(path, filename)
        except PermissionError:
            app.print_error('general', 'Kann File nicht öffnen (fehlende Rechte).')
        self.dismiss_popup()

class LoadDialog(GridLayout):
    import_data = ObjectProperty(None)
    cancel = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)
        app = App.get_running_app()

class SaveDialog(GridLayout):
    export_data = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)
        app = App.get_running_app()

class PlayerPage(Widget):    
    def __init__(self, **kwargs):
        super(PlayerPage, self).__init__(**kwargs)
        app = App.get_running_app()
        
        Clock.schedule_once(lambda dt: self.print_pool(app.players), 0.5)
    
    # Print the player pools to according labels
    def print_pool(self, players):
        self.ids.container.clear_widgets()
        if players == {}:
            self.add_row('', '', '', '', '')
            self.add_row('', 'Keine Spieler', '', '', '')
        else:
            self.add_row('', '', 'Spiele', 'Siege', 'Ballverh.')
            players_sort = {}
            for name in sorted(players.keys(), key=lambda x:str(x).lower()): 
                players_sort[name] = players[name]
            players_1 = [name for name in players_sort.keys() if players_sort[name].pool == 0]
            players_2 = [name for name in players_sort.keys() if players_sort[name].pool == 1]
            players_bench = [name for name in players_sort.keys() if players_sort[name].pool == 2]
            
            pool = 'Herren'
            for name in players_1:
                points_diff = str(players[name].points_won) + ':' + str(players[name].points_lost)
                self.add_row(pool, name, str(players[name].played), str(players[name].wins), points_diff)
                pool = ''
            self.add_row('', '', '', '', '')
            pool = 'Damen'
            for name in players_2:
                points_diff = str(players[name].points_won) + ':' + str(players[name].points_lost)
                self.add_row(pool, name, str(players[name].played), str(players[name].wins), points_diff)
                pool = ''
            self.add_row('', '', '', '', '')
            pool = 'Pausiert'
            for name in players_bench:
                points_diff = str(players[name].points_won) + ':' + str(players[name].points_lost)
                self.add_row(pool, name, str(players[name].played), str(players[name].wins), points_diff)
                pool = ''
                    
    def add_row(self, pool, name, num_games, points, points_diff):
        new_row = PlayerRow()
        self.ids.container.add_widget(new_row)
        new_row.ids.pool.text = pool
        new_row.ids.name.text = name
        new_row.ids.games.text = num_games
        new_row.ids.points.text = points
        new_row.ids.points_diff.text = points_diff

    def show_placements(self):
        content = Placements(close=self.dismiss_popup)
        self._popup = Popup(title='Platzierungen', content=content,
                            size_hint=(1, 1))
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

class PlayerRow(GridLayout):
    def __init__(self, **kwargs):
        super(PlayerRow, self).__init__(**kwargs)
        app = App.get_running_app()

class Placements(GridLayout):
    first = StringProperty('')
    second = StringProperty('')
    third = StringProperty('')
    
    close = ObjectProperty
    
    def __init__(self, close, **kwargs):
        super(Placements, self).__init__(**kwargs)
        app = App.get_running_app()
        
        self.close = close
        self.print_placement(app.players, app.points, app.ranking)
                
    def print_placement(self, players, points, ranking):
        self.ids.container.clear_widgets()
        
        players_1 = [name for name in sorted(players.keys()) if players[name].pool == 0]
        players_2 = [name for name in sorted(players.keys()) if players[name].pool == 1]
        
        tot_points = lambda x: ranking(players[x].wins,players[x].draws,players[x].points_won,players[x].points_lost)
        ranking_1 = sorted(players_1, key=tot_points, reverse=True)
        ranking_2 = sorted(players_2, key=tot_points, reverse=True)
        
        self.first = ''
        try:
            self.first += ranking_1[0]
            self.first += '\n'
        except IndexError:
            pass
        try:
            self.first += ranking_2[0]
        except IndexError:
            pass
        self.second = ''
        try:
            self.second += ranking_1[1]
            self.second += '\n'
        except IndexError:
            pass
        try:
            self.second += ranking_2[1]
        except IndexError:
            pass
        self.third = ''
        try:
            self.third += ranking_1[2]
            self.third += '\n'
        except IndexError:
            pass
        try:
            self.third += ranking_2[2]
        except IndexError:
            pass
        
        if len(players_1) > 0:
            self.add_row('[b]Herren[/b]', '', '', '', '')
            self.add_row('', '', '', '', '')
            self.add_row('Platz', 'Spieler', 'Spiele', 'Pkte.', 'Balldiff.')
            i=1
            for name in ranking_1:
                points_diff = str(players[name].points_won-players[name].points_lost)
                self.add_row(str(i), name, str(players[name].played), str(points(players[name].wins,players[name].draws)), points_diff)
                i+=1
            self.add_row('', '', '', '', '')
            self.add_row('', '', '', '', '')
        
        if len(players_2) > 0:
            self.add_row('[b]Damen[/b]', '', '', '', '')
            self.add_row('', '', '', '', '')
            self.add_row('Platz', 'Spieler', 'Spiele', 'Pkte.', 'Balldiff.')
            i=1
            for name in ranking_2:
                points_diff = str(players[name].points_won-players[name].points_lost)
                self.add_row(str(i), name, str(players[name].played), str(points(players[name].wins,players[name].draws)), points_diff)
                i+=1
                    
    def add_row(self, place, name, num_games, points, points_diff):
        new_row = PlacementsRow()
        self.ids.container.add_widget(new_row)
        new_row.ids.place.text = place
        new_row.ids.name.text = name
        new_row.ids.games.text = num_games
        new_row.ids.points.text = points
        new_row.ids.points_diff.text = points_diff
            
class PlacementsRow(GridLayout):
    def __init__(self, **kwargs):
        super(PlacementsRow, self).__init__(**kwargs)
        app = App.get_running_app()

class PoolPage(Widget):
    def __init__(self, **kwargs):
        super(PoolPage, self).__init__(**kwargs)
        app = App.get_running_app()
        
    def adjust_pools(self, app):
        "Move players to another player pool or remove players from pool"
        pool_1 = [name.strip() for name in self.ids.player_to_1.text.split(',')]
        pool_1_copy = pool_1.copy()
        pool_2 = [name.strip() for name in self.ids.player_to_2.text.split(',')]
        pool_2_copy = pool_2.copy()
        bench_player = [name.strip() for name in self.ids.bench_player.text.split(',')]
        bench_player_copy = bench_player.copy()
        delete_player = [name.strip() for name in self.ids.delete_player.text.split(',')]
        delete_player_copy = delete_player.copy()
        
        changed = 0
        
        if pool_1 != ['']:
            for name in pool_1:
                if name in app.players.keys():
                    app.players[name].switch_pool(0)
                    changed += 1
                    pool_1_copy.remove(name)
                    self.ids.player_to_1.text = ','.join(pool_1_copy)
                else:
                    app.players[name] = Player(name, 0)
                    changed += 1
                    pool_1_copy.remove(name)
                    self.ids.player_to_1.text = ','.join(pool_1_copy)
        
        if pool_2 != ['']:
            for name in pool_2:
                if name in app.players.keys():
                    app.players[name].switch_pool(1)
                    changed += 1
                    pool_2_copy.remove(name)
                    self.ids.player_to_2.text = ','.join(pool_2_copy)
                else:
                    app.players[name] = Player(name, 1)
                    changed += 1
                    pool_2_copy.remove(name)
                    self.ids.player_to_2.text = ','.join(pool_2_copy)

        if bench_player != ['']:
            for name in bench_player:
                try:
                    app.players[name].switch_pool(2)
                    changed += 1
                    bench_player_copy.remove(name)
                    self.ids.bench_player.text = ','.join(bench_player_copy)
                except KeyError:
                    app.print_error('player', 'Spieler {} exisitiert nicht.'.format(name))

        if delete_player != ['']:
            for name in delete_player:
                try:
                    app.players.pop(name)
                    changed += 1
                    delete_player_copy.remove(name)
                    self.ids.delete_player.text = ','.join(delete_player_copy)
                except KeyError:
                    app.print_error('player', 'Spieler {} exisitiert nicht.'.format(name))
                
        if changed > 0:
            app.save_status = False

class RoundPage(Widget):
    round = StringProperty('')
    score_1 = StringProperty('')
    score_2 = StringProperty('')
    courts_mixed_preset = StringProperty('')
    courts_pool_1_preset = StringProperty('')
    courts_pool_2_preset = StringProperty('')
    results_round = StringProperty('')
    results_court = StringProperty('')
    
    def __init__(self, **kwargs):
        super(RoundPage, self).__init__(**kwargs)
        app = App.get_running_app()
        self.round = str(app.next_round)
        self.courts_mixed_preset = str(3)
        self.courts_pool_1_preset = str(0)
        self.courts_pool_2_preset = str(0)
        self.results_round = self.round
        self.results_court = str(1)
    
    def new_round(self, app):
        self.round = str(app.next_round)
        try:
            self.courts_mixed = int(self.ids.courts_mixed.text)
        except ValueError:
            app.print_error('round', 'Anzahl der Mixed-Felder angeben. Setze 1.')
            self.courts_mixed = 1
            self.ids.courts_mixed.text = str(1)
        try:
            self.courts_pool_1 = int(self.ids.courts_pool_1.text)
        except ValueError:
            app.print_error('round', 'Anzahl der Herren-Felder angeben. Setze 0.')
            self.courts_pool_1 = 0
            self.ids.courts_pool_1.text = str(0)
        try:
            self.courts_pool_2 = int(self.ids.courts_pool_2.text)
        except ValueError:
            app.print_error('round', 'Anzahl der Damen-Felder angeben. Setze 0.')
            self.courts_pool_2 = 0
            self.ids.courts_pool_2.text = str(0)

        self.current = Round(app.next_round, self.courts_mixed, app.players, self.courts_pool_1, self.courts_pool_2, num_tries = app.num_tries)
        
        if self.current.pool_1_courts < self.courts_pool_1:
            app.print_error('round', 'Nicht genug Spieler / Paarungen. Belege nur {} Herren Felder.'.format(self.current.pool_1_courts))
        if self.current.pool_2_courts < self.courts_pool_2:
            app.print_error('round', 'Nicht genug Spieler / Paarungen. Belege nur {} Damen Felder.'.format(self.current.pool_2_courts))
        if self.current.mixed_courts < self.courts_mixed:
            app.print_error('round', 'Nicht genug Spieler / Paarungen. Belege nur {} Mixed Felder.'.format(self.current.mixed_courts))
        
        self.print_round(app)
        
        if len(self.current.teams) > 0:
            app.round_save_status = False
        else:
            del self.current
    
    def print_round(self, app):
        self.ids.container.clear_widgets()
        court = 0
        for i in range(self.current.pool_1_courts):
            self.add_row(court+1, self.current.teams[2*court], self.current.teams[2*court+1])
            court += 1          
        for i in range(self.current.pool_2_courts):
            self.add_row(court+1, self.current.teams[2*court], self.current.teams[2*court+1])
            court += 1   
        for i in range(self.current.mixed_courts):
            self.add_row(court+1, self.current.teams[2*court], self.current.teams[2*court+1])
            court += 1
            
    def pass_round(self, app):
        self.results_round = self.round
        self.results_court = str(1)
        app.rounds[app.next_round] = self.current
        app.next_round += 1
        for team in self.current.teams:
            app.players[team[0]].play(team[1])
            app.players[team[1]].play(team[0])
        app.round_save_status = True
        app.save_status = False
        try:
            self.courts_mixed_preset = self.ids.courts_mixed.text
        except ValueError:
            self.courts_mixed_preset = str(3)
        try:
            self.courts_pool_1_preset = self.ids.courts_pool_1.text
        except ValueError:
            self.courts_pool_1_preset = str(0)
        try:
            self.courts_pool_2_preset = self.ids.courts_pool_2.text
        except ValueError:
            self.courts_pool_1_preset = str(0)
            
    def resolve_round(self, app):
        try:
            round = int(self.ids.round.text)
            court = int(self.ids.court.text)
            try:
                score_1 = int(self.ids.score_1.text)
                score_2 = int(self.ids.score_2.text)
                success = app.rounds[round].resolve(app.players, court, score_1, score_2)
                if success == 1:
                    app.save_status = False
                    self.results_court = str(court+1)
                else:
                    app.print_error('round', 'Spielstand bereits eingegeben.')
            except KeyError:
                app.print_error('round', 'Rundennummer existiert nicht.')
            except IndexError:
                app.print_error('round', 'Spielfeld existiert nicht in dieser Runde.')
            except ValueError:
                app.print_error('round', 'Finalen Spielstand eingeben.')
        except ValueError:
            app.print_error('round', 'Runde und Feld eingeben (siehe Verlauf).')
        
    def add_row(self, court, team_1, team_2):
        new_row = NewRoundRow()
        self.ids.container.add_widget(new_row)
        new_row.ids.court.text = 'Feld {}:'.format(court)
        new_row.ids.current_team_1.text = '{}   &   {}'.format(team_1[0],team_1[1])
        new_row.ids.current_team_2.text = '{}   &   {}'.format(team_2[0],team_2[1])

class NewRoundRow(GridLayout):
    def __init__(self, **kwargs):
        super(NewRoundRow, self).__init__(**kwargs)
        app = App.get_running_app()

class TournamentPage(Widget):
    def __init__(self, **kwargs):
        super(TournamentPage, self).__init__(**kwargs)
        app = App.get_running_app()
        
        Clock.schedule_once(lambda dt: self.print_matchups(app.rounds), 0.5)

    def print_matchups(self, rounds):
        self.ids.container.clear_widgets()
        self.add_row('Runde', 'Team 1', 'Team 2', 'Score')
        if rounds == {}:
            self.add_row('-', '-', '-', '-:-')
        else:
            for number, round in rounds.items():
                if number < 10:
                    number = '0' + str(number)
                for i in range(len(round.matches)):
                    match = '{} {}'.format(number, i+1)
                    team_1 = '{}  &  {}'.format(round.matches[i].team_1[0] ,round.matches[i].team_1[1])
                    team_2 = '{}  &  {}'.format(round.matches[i].team_2[0], round.matches[i].team_2[1])
                    if round.matches[i].score_1 is not None:
                        score = '{} : {}'.format(round.matches[i].score_1, round.matches[i].score_2)
                    else:
                        score = '- : -'
                    self.add_row(match, team_1, team_2, score)
                    
        
    def add_row(self, round, team_1, team_2, score):
        new_row = TournamentRow()
        self.ids.container.add_widget(new_row)
        new_row.ids.round.text = round
        new_row.ids.team_1.text = team_1
        new_row.ids.team_2.text = team_2
        new_row.ids.score.text = score

class TournamentRow(GridLayout):
    def __init__(self, **kwargs):
        super(TournamentRow, self).__init__(**kwargs)
        app = App.get_running_app()

class TurnierApp(App):
    # Setup app variables
    version = 'v1.5.3'
    
    players, rounds = None, None
    next_round = None
    
    save_status = BooleanProperty(True)
    
    message_log_player = StringProperty('')
    message_log_round = StringProperty('')
    message_list = {'round':[], 'player':[], 'general':[]}
    
    round_save_status = BooleanProperty(True)
    
    apply_changes = BooleanProperty(True)
    change_message = StringProperty('')
    
    current_savefile = StringProperty('')
    
    save_files = StringProperty('')
    save_dates = StringProperty('')
    
    players_dict = {'name':'Name', 'pool':'Spieler-Pool', 'played':'Spiele', 'wins':'Siege', 'draws':'Unentschieden', 'points_won':'Gewonnene Bälle', 'points_lost':'Verlorene Bälle', 'team_mates':'Teampartner'}
    pool_dict = {0:'Herren', 1:'Damen', 2:'Pausiert'}
    rounds_dict = {'round_number':'Runde', 'court':'Feld', 'team_1':'Team 1', 'team_2':'Team 2', 'score_1':'Score Team 1', 'score_2':'Score Team 2'}

    def __init__(self, filename_players, filename_tournament, default_name, num_tries, points, ranking, **kwargs):
        super(TurnierApp, self).__init__(**kwargs)
        
        self.num_tries = num_tries
        self.points = points
        self.ranking = ranking
        root_folder = self.user_data_dir
        self.cache_folder = os.path.join(root_folder, 'cache')
        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)
        
        self.file_players_ending = filename_players
        self.file_tournament_ending = filename_tournament
        
        self.file_players = default_name + self.file_players_ending
        self.file_tournament = default_name + self.file_tournament_ending
        self.current_savefile = default_name
    
    def build(self):
        self.read_data()
        
        # Define platform specific scaling and root path
        if platform == 'android':
            self.savepath = '/storage/emulated/0/'
            self.scaling = 1
        else:
            self.savepath = os.getcwd()
            self.scaling = 0.3
            Window.size = (1080*self.scaling, 1920*self.scaling)
        
        # Define sizes of elements
        self.padding = 50 * self.scaling
        self.font_size_text = 36 * self.scaling
        self.font_size_button = 32 * self.scaling
        self.font_size_header = 46 * self.scaling
        self.font_size_notification = 24 * self.scaling
        self.row_height = self.font_size_text * 2
        self.button_height = 2*self.row_height
        
        tournament = MainScreen()
        
        return tournament
    
    def print_error(self, page, text):
        "Print message to console and the app's message_log"
        self.message_list[page] += [text]
        if page == 'round':
            self.message_log_round = ''
            self.message_log_round += '\n'.join(self.message_list[page][-5:])
        elif page == 'player':
            self.message_log_player = ''
            self.message_log_player += '\n'.join(self.message_list[page][-5:])
        print(text)
    
        Clock.schedule_once(lambda x: self.clear_error(text, page), 5)
        
    def clear_error(self, text, page = None):
        self.message_list[page].remove(text)
        if page == 'round':
            self.message_log_round = ''
            self.message_log_round += '\n'.join(self.message_list[page][-4:])
        elif page == 'player':
            self.message_log_player = ''
            self.message_log_player += '\n'.join(self.message_list[page][-4:])

    def read_data(self):
        "Set up players and rounds dicts and read data from files"
        filepath_players = os.path.join(self.cache_folder, self.file_players)
        filepath_tournament = os.path.join(self.cache_folder, self.file_tournament)
        
        self.players = {}
        self.rounds = {}
        
        try:
            converters_players = {'team_mates':eval}
            converters_rounds = {'team_1':eval, 'team_2':eval}
            players_df = pd.read_csv(filepath_players, index_col=0, converters=converters_players)
            players_df = players_df.astype({'pool':int, 'played':int, 'wins':int, 'draws':int, 'points_won':int, 'points_lost':int})
            rounds_df = pd.read_csv(filepath_tournament, index_col=False, converters=converters_rounds)
            rounds_df = rounds_df.fillna(-1)
            rounds_df = rounds_df.astype({'score_1':int, 'score_2':int})    
            self.update_from_df(players_df, rounds_df)
        except FileNotFoundError:
            self.next_round = 1
        
        self.save_status = True
        self.print_saves()
        
    def import_data(self, path, filename):
        self.current_savefile = os.path.basename(filename.replace('.xlsx', ''))
        self.file_players = self.current_savefile + self.file_players_ending
        self.file_tournament = self.current_savefile + self.file_tournament_ending
                
        inv_players_dict = {v: k for k, v in self.players_dict.items()}
        inv_pool_dict = {v: k for k, v in self.pool_dict.items()}
        inv_rounds_dict = {v: k for k, v in self.rounds_dict.items()}
        
        players_df = pd.read_excel(filename, 0, index_col=False, engine='openpyxl')
        rounds_df = pd.read_excel(filename, 1, index_col=False, engine='openpyxl')
        rounds_df = rounds_df.fillna(-1)
        
        players_df.rename(columns=inv_players_dict, inplace=True)
        players_df['pool'].replace(inv_pool_dict, inplace=True)
        players_df['team_mates'] = players_df['team_mates'].apply(lambda x: x.split(', ') if pd.notna(x) else [])
        rounds_df.rename(columns=inv_rounds_dict, inplace=True)
        rounds_df['court'] = rounds_df['court'].apply(lambda x: x - 1)
        rounds_df['team_1'] = rounds_df['team_1'].apply(lambda x:  tuple(x.split(', ')))
        rounds_df['team_2'] = rounds_df['team_2'].apply(lambda x:  tuple(x.split(', ')))
        
        players_df = players_df.astype({'pool':int, 'played':int, 'wins':int, 'draws':int, 'points_won':int, 'points_lost':int})
        rounds_df = rounds_df.astype({'score_1':int, 'score_2':int})
        
        self.players = {}
        self.rounds = {}
        self.update_from_df(players_df, rounds_df)
    
    def update_from_df(self, players_df, rounds_df):
        for index, row in players_df.iterrows():
            name = str(row['name'])
            self.players[name] = Player(*row)
        for round_number in rounds_df['round_number'].unique():
            courts = rounds_df[rounds_df['round_number'] == round_number].court.max()+1
            teams = []
            scores = []
            for i, row in rounds_df[rounds_df['round_number'] == round_number].iterrows():
                teams.append(row.team_1)
                teams.append(row.team_2)
                if row.score_1 > 0:
                    scores.append(row.score_1)
                    scores.append(row.score_2)
                else:
                    scores.append(None)
                    scores.append(None)
            self.rounds[round_number] = Round(round_number, courts, None, teams=teams, scores=scores)
            
        self.next_round = len(self.rounds)+1
    
    def update_data(self, new_filename):
        self.current_savefile = new_filename
        self.file_players = self.current_savefile + self.file_players_ending
        self.file_tournament = self.current_savefile + self.file_tournament_ending
        self.save_status = False
    
    def save_data(self, path=None, filename=None):
        filepath_players = os.path.join(self.cache_folder, self.file_players)
        filepath_tournament = os.path.join(self.cache_folder, self.file_tournament)
                
        players_df, rounds_df = self.create_dfs()
        players_df.to_csv(filepath_players)
        rounds_df.to_csv(filepath_tournament)
        
        self.save_status = True
        self.print_saves()
        
    def export_data(self, path, filename):
        if not filename:
            filename = os.path.join(path, self.current_savefile+'.xlsx')
        elif '.xlsx' not in filename:
            filename = os.path.join(path, filename+'.xlsx')
        else:
            filename = os.path.join(path, filename)
        
        players_df, rounds_df = self.create_dfs()
        
        players_df.rename(columns=self.players_dict, inplace=True)
        players_df[self.players_dict['pool']].replace(self.pool_dict, inplace=True)
        players_df[self.players_dict['team_mates']] = players_df[self.players_dict['team_mates']].apply(lambda x: (str(x)[1:-1]).replace('\'', ''))
        rounds_df.rename(columns=self.rounds_dict, inplace=True)
        rounds_df[self.rounds_dict['court']] = rounds_df[self.rounds_dict['court']].apply(lambda x: x + 1)
        rounds_df[self.rounds_dict['team_1']] = rounds_df[self.rounds_dict['team_1']].apply(lambda x: (str(x)[1:-1]).replace('\'', ''))
        rounds_df[self.rounds_dict['team_2']] = rounds_df[self.rounds_dict['team_2']].apply(lambda x: (str(x)[1:-1]).replace('\'', ''))
        
        with pd.ExcelWriter(filename) as writer:
            players_df.to_excel(writer, sheet_name='Spieler', index=False)
            rounds_df.to_excel(writer, sheet_name='Runden', index=False)
    
    def create_dfs(self):
        players_df = pd.DataFrame({'name':[], 'pool':[], 'played':[], 'wins':[], 'draws':[], 'points_won':[], 'points_lost':[], 'team_mates':[]})
        players_df = players_df.astype({'pool':int, 'played':int, 'wins':int, 'draws':int, 'points_won':int, 'points_lost':int})
        for name, player in self.players.items():
            players_df = players_df.append({'name':name, 'pool':player.pool, 'played':player.played, 'wins':player.wins, 'draws':player.draws, 'points_won':player.points_won, 'points_lost':player.points_lost, 'team_mates':player.team_mates}, ignore_index=True)
        
        rounds_df = pd.DataFrame({'round_number':[], 'court':[], 'team_1':[], 'team_2':[], 'score_1':[], 'score_2':[]})
        rounds_df = rounds_df.astype({'round_number':int, 'court':int, 'score_1':int, 'score_2':int})
        for number, round in self.rounds.items():
            for match in round.matches:
                rounds_df = rounds_df.append({'round_number':match.round_number, 'court':match.court, 'team_1':match.team_1, 'team_2':match.team_2, 'score_1':match.score_1, 'score_2':match.score_2}, ignore_index=True)
        
        return players_df, rounds_df
    
    def delete(self):
        filepath_players = os.path.join(self.cache_folder, self.file_players)
        filepath_tournament = os.path.join(self.cache_folder, self.file_tournament)
        try:
            os.remove(filepath_players)
            os.remove(filepath_tournament)
            self.read_data()
            self.print_saves()
        except:
            self.print_error('general', 'File existiert nicht.')
        
    def print_saves(self):
        files = list(set([f.replace(self.file_players_ending,'').replace(self.file_tournament_ending,'') for f in os.listdir(self.cache_folder)]))
        
        if files:
            modification_times = [os.path.getmtime(os.path.join(self.cache_folder,f+self.file_players_ending)) for f in files]
            
            sort = sorted(zip(modification_times, files), reverse=True)
            modification_times, files = zip(*sort)
            
            modification_times = [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(times)) for times in modification_times]
            
            self.save_files = '[b]Gespeicherte Turniere:[/b]\n'
            self.save_files += '\n'.join(files)
            self.save_dates = 'Änderungsdatum\n'
            self.save_dates += '\n'.join(modification_times)
        else:
            self.save_files = ''
            self.save_dates = ''

if __name__ == '__main__':
    import bugs
    bugs.fixBugs()
    
    from player import Player
    from round import Round
    
    TurnierApp(filename_players_init, filename_tournament_init, default_name_init, num_tries_init, points_init, ranking_init).run()