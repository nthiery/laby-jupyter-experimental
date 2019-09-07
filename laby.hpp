std::string utf8_substr(const std::string& str, unsigned int start, unsigned int leng)
{
    if (leng==0) { return ""; }
    unsigned int c, i, ix, q;
    unsigned long min=std::string::npos, max=std::string::npos;
    for (q=0, i=0, ix=str.length(); i < ix; i++, q++)
    {
        if (q==start){ min=i; }
        if (q<=start+leng || leng==std::string::npos){ max=i; }

        c = (unsigned char) str[i];
        if      (
                 //c>=0   &&
                 c<=127) i+=0;
        else if ((c & 0xE0) == 0xC0) i+=1;
        else if ((c & 0xF0) == 0xE0) i+=2;
        else if ((c & 0xF8) == 0xF0) i+=3;
        //else if (($c & 0xFC) == 0xF8) i+=4; // 111110bb //byte 5, unnecessary in 4 byte UTF-8
        //else if (($c & 0xFE) == 0xFC) i+=5; // 1111110b //byte 6, unnecessary in 4 byte UTF-8
        else return "";//invalid utf8
    }
    if (q<=start+leng || leng==std::string::npos){ max=i; }
    if (min==std::string::npos || max==std::string::npos) { return ""; }
    return str.substr(min,max-min);
}

unsigned char utf8_len(const std::string& str)
{
    unsigned int l=0;
    unsigned int c;
    for ( unsigned int i=0; i < str.length(); i++, l++ )
    {
        c = (unsigned char) str[i];
        if      (
                 c<=127) i+=0;
        else if ((c & 0xE0) == 0xC0) i+=1;
        else if ((c & 0xF0) == 0xE0) i+=2;
        else if ((c & 0xF8) == 0xF0) i+=3;
        else throw runtime_error("invalid utf8");
    }
    return l;
}

struct Position {
    int i;
    int j;
};

enum class Direction { North, West, South, East };
vector<Position> directions = { {-1,0}, {-0,1}, {1,0}, {0,1} };

enum Tile {
    AntE, AntN, AntS, AntW, Exit, SmallRock, SmallWeb, Rock, Void, Wall, Web
};

vector<string> tilenames = {
    "ant-e.png", "ant-n.png", "ant-s.png", "ant-w.png", "exit.png", "nrock.png", "nweb.png", "rock.png", "void.png", "wall.png", "web.png"
};
vector<string> tilechars = {
    u8"→", u8"↑", u8"↓", u8"←", "x", "?", "?", "r", ".", "o", "w"
};

vector<Tile> ant_tiles = { AntN, AntW, AntS, AntE };

Tile char_to_tile(string c) {
    for ( unsigned int i=0; i < tilechars.size(); i++ ) {
        if ( c == tilechars[i] ) {
            return Tile(i);
        }
    }
    throw runtime_error("no tile found");
}

using Board = vector<vector<Tile>>;

class Labyrinth {
    Board board;
    Position position;
    Direction direction=Direction::North;
    public:
    Labyrinth() {
    }
    Labyrinth(string s) {
        from_string(s);
    }
    void load(string file) {
        ifstream fd;
        fd.open(file);
        string line;
        string s;
        getline(fd, line);
        getline(fd, line);
        while ( line.size() > 0 ) {
            s += line;
        }
        from_string(s);
        fd.close();
    }
    void from_string(string s) {
        board = Board();
        istringstream fd(s);
        string l;
        int i = 0;
        while ( getline(fd, l) ) {
            vector<Tile> line;
            for (int j = 0; 2*j < utf8_len(l); j++) {
                Tile tile = char_to_tile(utf8_substr(l, 2*j,1));
                for (unsigned int dir = 0; dir < 4; dir ++) {
                    if ( tile == ant_tiles[dir] ) {
                        position = { i, j };
                        direction = Direction(dir);
                        tile = Tile::Void;
                        break;
                    }
                }
                line.push_back(tile);
            }
            board.push_back(line);
            i++;
        }
    }

    string to_string() {
        string s = "";
        for ( auto line: view() ) {
            for (int j=0; j<line.size(); j++ ) {
                s += tilechars[line[j]];
                if ( j < line.size() - 1 )
                    s+= " ";
            }
            s += "\n";
        }
        return s;
    }

    Board view() {
        Board view = board;
        view[position.i][position.j] = ant_tiles[int(direction)];
        return view;
    }
    void win() {
    }
    bool gauche() {
        switch (direction) {
        case Direction::North: direction=Direction::West;  break;
        case Direction::East:  direction=Direction::North; break;
        case Direction::South: direction=Direction::East;  break;
        case Direction::West:  direction=Direction::South; break;
        }
        return true;
    }
    bool droite() {
        switch (direction) {
        case Direction::North: direction=Direction::East;  break;
        case Direction::East:  direction=Direction::South; break;
        case Direction::South: direction=Direction::West;  break;
        case Direction::West:  direction=Direction::North; break;
        }
        return true;
    }
    bool avance() {
        Tile tile = board[position.i][position.j];
        if ( tile == Tile::Web )  return false;
        if ( tile == Tile::Exit ) return false;

        Position diff = directions[int(direction)];
        Position new_position = Position({position.i+diff.i,position.j+diff.j});
        if (new_position.i < 0 or
            new_position.j < 0 or
            new_position.i >= board.size() or
            new_position.j >= board[0].size()) {
            return false;
        }
        tile = board[new_position.i][new_position.j];
        if ( tile == Tile::Rock or tile == Tile::Wall ) return false;
        position = new_position;
        if ( tile == Tile::Exit ) {
            win();
        }
        return true;
    }
};

class LabyrinthView {
    public:
    Board value;
};

class Player {
    LabyrinthView view;
    vector<Board> history;
    int time;
    Player(LabyrinthView _view) {
        view = _view;
        time = 0;
        history.push_back(view.value);
    }
    void update() {
        view.value = history[time];
    }
    void set_value(Board value) {
        history.push_back(value);
        if ( time == history.size() - 1 ) {
            time++;
            update();
        }
    }
    void begin() {
        time = 0;
        update();
    }
    void end() {
        time = history.size() - 1;
        update();
    }
    void back() {
        if ( time > 0 ) {
            time--;
            update();
        }
    }
    void forward() {
        if ( time < history.size() - 1 ) {
            time++;
            update();
        }
    }
};
