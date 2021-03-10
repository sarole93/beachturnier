class Player:
    "Player has a name, pool (0, 1, 2) and tournament statistics (#games played, wins, draws, points won and lost and previous team mates."
    def __init__(self, name, pool, played = 0, wins = 0, draws = 0, points_won = 0, points_lost = 0, team_mates = None):
        self.name = name
        self.pool = pool
        self.played = played
        self.wins = wins
        self.draws = draws
        self.points_won = points_won
        self.points_lost = points_lost
        if team_mates is None:
            self.team_mates = []
        else:
            self.team_mates = [x for x in team_mates if x]

    def __repr__(self):
        return '{}: {} Spiel(e), {} Sieg(e)'.format(self.name, self.played, self.wins)
    
    def play(self, partner):
        "Update stats when playing with partner."
        self.played += 1
        self.team_mates.append(partner)

    def win(self, score_1, score_2):
        "Update stats when winning. Scores are not ordered."
        self.wins += 1
        if score_1 > score_2:
            self.points_won += score_1
            self.points_lost += score_2
        elif score_2 > score_1:
            self.points_won += score_2
            self.points_lost += score_1

    def draw(self, score_1, score_2):
        "Update stats in case of draw."
        self.draws += 1
        self.points_won += score_1
        self.points_lost += score_1
        
    def lose(self, score_1, score_2):
        "Update stats when losing. Scores are not ordered."
        if score_1 > score_2:
            self.points_won += score_2
            self.points_lost += score_1
        elif score_2 > score_1:
            self.points_won += score_1
            self.points_lost += score_2

    def switch_pool(self, new_pool = None):
        "Switch between pool 0 and 1 or to new_pool"
        if new_pool is None:
            self.pool = 1 - self.pool
        else:
            self.pool = new_pool