import random
import pandas as pd

class Match:
    "Each Match carries round number, the court it's played on and the two teams and scores."
    def __init__(self, round_number, court, team_1, team_2, score_1 = None, score_2 = None):
        self.round_number = round_number
        self.court = court
        self.team_1 = team_1
        self.team_2 = team_2
        self.score_1 = score_1
        self.score_2 = score_2
        if self.score_1 is None:
            self.locked = 0
        else:
            self.locked = 1
    def __repr__(self):
        return 'Runde {}, Feld {}:  {}  vs  {}  ({}:{})'.format(self.round_number, self.court+1, self.team_1, self.team_2, self.score_1, self.score_2)

class Round:
    "A Round is initialized with the round number, the number of courts played and the players."
    def __init__(self, number, courts_mixed, players, pool_1_courts = 0, pool_2_courts = 0, teams = None, scores = None, num_tries = 1):
        self.number = number
        self.mixed_courts = courts_mixed
        self.pool_1_courts = pool_1_courts
        self.pool_2_courts = pool_2_courts
        self.courts = self.mixed_courts + self.pool_1_courts + self.pool_2_courts
        if teams is None:
            self.teams = self.draw_teams(players, 2 * courts_mixed, 2 * pool_1_courts, 2 * pool_2_courts, num_tries)
        else:
            self.teams = teams
        self.matches = []
        for court in range(self.courts):
            if scores is None:
                self.matches.append(Match(self.number, court, self.teams[2*court], self.teams[2*court+1]))
            else:
                score_1 = scores[2*court]
                score_2 = scores[2*court+1]
                self.matches.append(Match(self.number, court, self.teams[2*court], self.teams[2*court+1], score_1, score_2))
      
    def draw_teams(self, players, n, n_1, n_2, num_tries):
        "Draw n mixed, n_1 pool-1 and n_2 pool-2 teams from players"
        players_1 = {name:players[name] for name in players.keys() if players[name].pool == 0}
        players_2 = {name:players[name] for name in players.keys() if players[name].pool == 1}
        
        n_mixed_init = n
        
        #Calculate max number of teams possible at given player pool
        n_1_max = int((len(players_1) - len(players_1) % 2) / 2)
        if n_1 > n_1_max:
            n_1 = n_1_max - (n_1_max % 2)
        n_2_max = int((len(players_2) - len(players_2) % 2) / 2)
        if n_2 > n_2_max:
            n_2 = n_2_max - (n_2_max % 2)
        n_max = min([len(players_1)-2*n_1, len(players_2)-2*n_2])
        n_max_init = min([len(players_1), len(players_2), n_mixed_init])
        if n > n_max:
            n = n_max - (n_max % 2)
        
        n_1_filled = 0
        n_2_filled = 0
        n_filled = 0
        teams_pool_1 = []
        teams_pool_2 = []
        teams_mixed = []
        tries_max = num_tries
        
        # while not all teams are filled as desired draw pairs
        while n_filled < n_max_init or n_1_filled < n_1 or n_2_filled < n_2:
            players_1_copy = players_1.copy()
            players_2_copy = players_2.copy()  
            tries = 0
            
            # try tries_max times to draw as desired
            while (n_1_filled < n_1 or n_2_filled < n_2 or n_filled < n) and tries < tries_max:
                try:
                    num_chosen_1 = min((n-n_filled)+2*(n_1-n_1_filled), len(players_1_copy))
                    num_chosen_2 = min((n-n_filled)+2*(n_2-n_2_filled), len(players_2_copy))
                    if num_chosen_1 == 0:
                        pool_1_chosen = []
                    else: 
                        pool_1_chosen = self.weighted_choice(players_1_copy, num_chosen_1)
                    if num_chosen_2 == 0:
                        pool_2_chosen = []
                    else: 
                        pool_2_chosen = self.weighted_choice(players_2_copy, num_chosen_2)
                    elig_partners = {}
                    elig_partners_1 = {}
                    elig_partners_2 = {}
                    chosen_set = set(pool_1_chosen).union(set(pool_2_chosen))
                    chosen_1_set = set(pool_1_chosen)
                    chosen_2_set = set(pool_2_chosen)
                    for player in pool_1_chosen:
                        unelig = set([name for name in players[player].team_mates])
                        unelig.add(player)
                        elig_partners[player] = list(chosen_set.difference(unelig))
                        elig_partners_1[player] = list(chosen_1_set.difference(unelig))
                        elig_partners_2[player] = list(chosen_2_set.difference(unelig))
                    for player in pool_2_chosen:
                        unelig = set([name for name in players[player].team_mates])
                        unelig.add(player)
                        elig_partners[player] = list(chosen_set.difference(unelig))
                        elig_partners_1[player] = list(chosen_1_set.difference(unelig))
                        elig_partners_2[player] = list(chosen_2_set.difference(unelig))
                    
                    # start with player who has the least options in partners
                    players_ranked = sorted(elig_partners, key=lambda x: len(elig_partners[x]))
                    chosen_1 = players_ranked[0]
                    
                    # unless this already failed multiple times
                    if tries > tries_max/2:
                        chosen_1 = random.choice(players_ranked)
                    
                    # failed to find team if chosen player cannot play with anyone
                    if len(elig_partners[chosen_1]) == 0:
                        tries += 1
                    else:
                        # choose player 2 from appropriate pool
                        chosen_2 = random.choice(elig_partners[chosen_1])
                        if chosen_1 in pool_1_chosen:
                            if n_1_filled == n_1:
                                chosen_2 = random.choice(elig_partners_2[chosen_1])
                            elif n_filled == n:
                                chosen_2 = random.choice(elig_partners_1[chosen_1])
                        if chosen_1 in pool_2_chosen:
                            if n_2_filled == n_2:
                                chosen_2 = random.choice(elig_partners_1[chosen_1])
                            elif n_filled == n:
                                chosen_2 = random.choice(elig_partners_2[chosen_1])
                        # add new team to correct list and remove them from further player draws
                        if chosen_1 in pool_1_chosen:
                            if chosen_2 in pool_1_chosen:
                                if n_1_filled < n_1:
                                    teams_pool_1 += [(chosen_1, chosen_2)]
                                    n_1_filled += 1
                                    players_1_copy.pop(chosen_1)
                                    players_1_copy.pop(chosen_2)
                            elif chosen_2 in pool_2_chosen:
                                if n_filled < n:
                                    teams_mixed += [(chosen_1, chosen_2)]
                                    n_filled += 1
                                    players_1_copy.pop(chosen_1)
                                    players_2_copy.pop(chosen_2)
                        if chosen_1 in pool_2_chosen:
                            if chosen_2 in pool_1_chosen:
                                if n_filled < n:
                                    teams_mixed += [(chosen_2, chosen_1)]
                                    n_filled += 1
                                    players_2_copy.pop(chosen_1)
                                    players_1_copy.pop(chosen_2)
                            elif chosen_2 in pool_2_chosen:
                                if n_2_filled < n_2:
                                    teams_pool_2 += [(chosen_2, chosen_1)]
                                    n_2_filled += 1
                                    players_2_copy.pop(chosen_1)
                                    players_2_copy.pop(chosen_2)
                except IndexError:
                    tries += 1
            
            # cut off teams at even numbers (see below)
            n_1_filled = int(n_1_filled - n_1_filled%2)
            n_2_filled = int(n_2_filled - n_2_filled%2)
            n_filled = int(n_filled - n_filled%2)
            
            # if pool 1 and 2 teams could not be filled, reattempt with mixed teams only
            if n_1_filled < n_1 or n_2_filled < n_2:
                for i in range(n_1_filled):
                    players_1.pop(teams_pool_1[i][0])
                    players_1.pop(teams_pool_1[i][1])
                for i in range(n_2_filled):
                    players_2.pop(teams_pool_2[i][0])
                    players_2.pop(teams_pool_2[i][1])
                for i in range(n_filled):
                    players_1.pop(teams_mixed[i][0])
                    players_2.pop(teams_mixed[i][1])
                n_1 = n_1_filled
                n_2 = n_2_filled
                n_max = min([len(players_1), len(players_2)])+n_filled
                if n_mixed_init > n_max:
                    n = n_max - (n_max % 2)
                else:
                    n = n_mixed_init
            else:
                break
            
            
        # cut off teams at even numbers
        teams_pool_1 = teams_pool_1[:n_1_filled]
        teams_pool_2 = teams_pool_2[:n_2_filled]
        teams_mixed = teams_mixed[:n_filled]
        
        # shuffle again internally so player who is chosen first doesn't always play on field 1
        random.shuffle(teams_pool_1)
        random.shuffle(teams_pool_2)
        random.shuffle(teams_mixed)
        
        # readjust number of courts used
        self.pool_1_courts = int(n_1_filled/2)
        self.pool_2_courts = int(n_2_filled/2)
        self.mixed_courts = int(n_filled/2)
        self.courts = self.mixed_courts + self.pool_1_courts + self.pool_2_courts
        
        teams = teams_pool_1 + teams_pool_2 + teams_mixed

        return teams

    def weighted_choice(self, players, n):
        "Draw a name from players dict, weighted by number of games already played."
        names, played = list(zip(*[(name, player.played) for name, player in players.items()]))
        weights = [(max(played)+1-p)**6 for p in played]
        df = pd.DataFrame({'name':names, 'weight':weights})
        chosen = (df.sample(n=n, replace=False, weights='weight'))['name'].tolist()
        return chosen

    def resolve(self, players, court, score_1, score_2):
        "Update Matches and Players for a given score."
        if self.matches[court-1].locked == 1:
            old_score_1 = self.matches[court-1].score_1
            old_score_2 = self.matches[court-1].score_2
            self.unresolve(players, court, old_score_1, old_score_2)
        if self.matches[court-1].locked == 0:
            self.matches[court-1].score_1 = score_1
            self.matches[court-1].score_2 = score_2
            if score_1 == score_2:
                players[self.teams[2*(court-1)][0]].draw(score_1, score_2)
                players[self.teams[2*(court-1)][1]].draw(score_1, score_2)
                players[self.teams[2*(court-1)+1][0]].draw(score_1, score_2)
                players[self.teams[2*(court-1)+1][1]].draw(score_1, score_2)
            else:
                if score_1 > score_2:
                    winner_1 = self.teams[2*(court-1)][0]
                    winner_2 = self.teams[2*(court-1)][1]
                    loser_1 = self.teams[2*(court-1)+1][0]
                    loser_2 = self.teams[2*(court-1)+1][1]
                elif score_2 > score_1:
                    winner_1 = self.teams[2*(court-1)+1][0]
                    winner_2 = self.teams[2*(court-1)+1][1]
                    loser_1 = self.teams[2*(court-1)][0]
                    loser_2 = self.teams[2*(court-1)][1]
                players[winner_1].win(score_1, score_2)
                players[winner_2].win(score_1, score_2)
                players[loser_1].lose(score_1, score_2)
                players[loser_2].lose(score_1, score_2)
            self.matches[court-1].locked = 1
            success = 1
        else:
            success = 0
        return success
    
    def unresolve(self, players, court, score_1, score_2):
        "Update Matches and Players for a given score."
        self.matches[court-1].score_1 = None
        self.matches[court-1].score_2 = None
        if score_1 == score_2:
            players[self.teams[2*(court-1)][0]].undraw(score_1, score_2)
            players[self.teams[2*(court-1)][1]].undraw(score_1, score_2)
            players[self.teams[2*(court-1)+1][0]].undraw(score_1, score_2)
            players[self.teams[2*(court-1)+1][1]].undraw(score_1, score_2)
        else:
            if score_1 > score_2:
                winner_1 = self.teams[2*(court-1)][0]
                winner_2 = self.teams[2*(court-1)][1]
                loser_1 = self.teams[2*(court-1)+1][0]
                loser_2 = self.teams[2*(court-1)+1][1]
            elif score_2 > score_1:
                winner_1 = self.teams[2*(court-1)+1][0]
                winner_2 = self.teams[2*(court-1)+1][1]
                loser_1 = self.teams[2*(court-1)][0]
                loser_2 = self.teams[2*(court-1)][1]
            players[winner_1].unwin(score_1, score_2)
            players[winner_2].unwin(score_1, score_2)
            players[loser_1].unlose(score_1, score_2)
            players[loser_2].unlose(score_1, score_2)
        self.matches[court-1].locked = 0