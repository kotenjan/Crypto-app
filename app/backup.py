from utils.backup import Backup


if __name__ == '__main__':
    Backup(60*60*24, 60*60*2).loop()
