import sys
from PyQt5.QtWidgets import QApplication
from functions import CatWidget, load_cat_folders, MousePressWatcher

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Dodajemy filtr myszy
    watcher = MousePressWatcher()
    app.installEventFilter(watcher)

    cat_folders = load_cat_folders("assets")
    cats = []

    for folder in cat_folders:
        cat = CatWidget(folder)
        cat.show()
        cats.append(cat)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()