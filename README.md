On hal21:

production: port 5050
dev: port 5051

# Setting up on hal21

    cd /t/planner.breathecam.org
    DEST=iter002
    sudo git clone --recursive https://github.com/CMU-CREATE-Lab/breathecam_view_planner.git $DEST
    cd $DEST
    sudo chown -R rsargent .

    /usr/bin/python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip

    pip install -r requirements.txt



# Running dev

Terminal/Run Build Task:  runs tsc in "watch" mode

Run flask on port 5051 on hal21, and it will receive proxying from https://planner-dev.breathecam.org

Using vscode: "debug" icon, then select python: flask and click green arrow "run" button.  It will run on port 5051

or: flask run --port 5051

Visit https://planner-dev.breathecam.org






* webpack

Reference: https://webpack.js.org/guides/typescript/

Reference: https://dev.to/anitaparmar26/webpack-5-guide-for-beginners-314c

    npm install webpack webpack-cli –-save-dev
    npm exec webpack
