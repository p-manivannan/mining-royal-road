

class NovelDeleted(Exception):
    '''Custom exception when novel is deleted'''
    def __init__(self, message="404 Error: Novel has been deleted"):
        self.message = message 
        super().__init__(self.message)