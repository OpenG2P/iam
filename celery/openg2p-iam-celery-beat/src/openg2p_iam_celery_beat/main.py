from .app import Initializer

initializer = Initializer()
initializer.initialize()

app = initializer.return_app()

if __name__ == "__main__":
    initializer.main()
