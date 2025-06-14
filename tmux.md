## Commands
```bash
tmux                         # Start a new session
tmux new -s <session-name>   # Create a named session
tmux attach -t <session>     # Attach to an existing session
tmux ls                      # List all sessions
tmux kill-session -t <name>  # Kill a specific session
```

## Shortcuts
| Shortcut       | Action                    |
| -------------- | ------------------------- |
| `Ctrl+b d`     | Detach from session       |
| `Ctrl+b %`     | Split window vertically   |
| `Ctrl+b "`     | Split window horizontally |
| `Ctrl+b o`     | Switch between panes      |
| `Ctrl+b x`     | Kill current pane         |
| `Ctrl+b c`     | Create a new window       |
| `Ctrl+b n / p` | Next / Previous window    |
| `Ctrl+b ,`     | Rename current window     |
| `Ctrl+b [`     | Scrollback mode           |
| `Ctrl+b :`     | Command prompt            |
| `Ctrl+b ->`    | Switch pane to right (l,u,d)  |

## Examples

Create four evenly sized panes, one for infra, rust and go. Consider `tmxdev.sh`

```sh
#!/bin/bash

SESSION="dev"

# Create the session only if it doesn't already exist
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    # Create session with first window: infra
    tmux new-session -d -s "$SESSION" -n infra

    # Add more windows
    tmux new-window -t "$SESSION":1 -n go-api
    tmux new-window -t "$SESSION":2 -n react-app

    # Define a layout function to split windows into 2x2
    for WIN in infra go-api react-app; do
        tmux select-window -t "$SESSION:$WIN"
        tmux split-window -h                   # Right split
        tmux split-window -v -t 0              # Bottom-left
        tmux split-window -v -t 1              # Bottom-right
        tmux select-layout tiled               # Arrange panes
    done
fi

# Attach to the session
tmux attach -t "$SESSION"
```

Then execute:
```bash
chmod +x tmxdev.sh
./tmxdev.sh
```