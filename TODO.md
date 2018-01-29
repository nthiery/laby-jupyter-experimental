# TODO

## Project setup

- [x] Learn git's and github's basics.
      E.g. from https://try.github.io/ or https://git-scm.com/docs/gittutorial
- [x] Create an account on GitHub and tell Nicolas to add you to the project
- [x] Clone this repository
- [x] Import artwork from laby's repo https://github.com/sgimenez/laby/
- [ ] Learn about using ssh keys to not have to type in your
      login/pass each time you push
- [ ] Install the required dependencies by creating a conda environment.
      Thanks to the environment.xml file is this project, you can just do:

        conda env create

- [ ] Update the file environment.xml as appropriate

## Experiment with widgets

- [x] Create a slider
- [ ] Create a widget displaying an image
- [ ] Create a widget displaying a grid of images, each being a separate widget
- [ ] Display one of laby's maze using the above

## Implement the model

- [ ] Define a type Cell (e.g. using an enum) to represent the content
      of a cell: Rock, Web, AntLeft, AntRight, ...

- [ ] Define a type Maze to represent a maze (a vector of vector of
      the above), and the position of the Ant

       maze[i][j]  ---->   Rock
       maze.ant_position()    ---> (3,1)
       maze.ant_direction()   ---> Up

- [ ] Implement functions (methods, constructors) to load / save a
      maze to disk, in laby's format

- [ ] Implement functions/methods for the actions of the ant: 

      maze.forward()
      maze.left()
      maze.right()
      maze.pickup()
      maze.open()

### WithHistory

- [ ] Define a type MazeWithHistory that keeps the history of all the
      intermediate step and enable going back in history.

      MazeWithHistory maze = MazeWithHistory();

      maze.forward();
      maze.left();
      maze.forward();
      maze.history_back();
      maze.history_backward();
      maze.history_forward();
      maze.history_start();
      maze.history_end();
      maze[i][j];                 the content of cell at the current step

      Perhaps it needs an attribute "synchronous" telling whether
      actions should update the "current step".

## Implement the view

- [ ] Implement a new widget MazeUI:

      Maze maze = Maze("1a.laby");
      MazeUI mazeUI = MazeUI(maze);
      mazeUI.display()

      maze.forward()
      mazeUI.update()

- [ ] Use the observer pattern so that the maze UI gets automatically
      updated?

- [ ] Write a demo notebook, with shorthands in the user's language:

      avance();
      droite();


- [ ] Implement a new widget MazeWithHistoryUI

      Same as above, with a UI to move through history (buttons play,
      forward, fast forward, backward, start, end), enabling step by
      step execution.

## Multithreading?

As long as the user's programs always terminate after a reasonable
amount of steps, we can afford to execute it all and record its the
full history before the user visualization / interaction. This gets
trickier.

## Notebooks

- [ ] Write a sketch notebook

      Requires: displaying one of laby's maze as above

      Include all the UI's:
      - a maze
      - buttons for step by step execution
      - a cell for the user to type in his cod
      - some text cells with explanations

- [ ] Write a collection of notebooks, one for each level
- [ ] Generate the notebooks automatically?
