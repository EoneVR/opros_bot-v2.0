import sqlite3


class Database:
    def __init__(self):
        self.database = sqlite3.connect('data.db', check_same_thread=False)
        self.create_users_table()
        self.create_polls_table()
        self.create_answers_table()

    def manager(self, sql, *args,
                fetchone: bool = False,
                fetchall: bool = False,
                commit: bool = False):
        with self.database as db:
            cursor = db.cursor()
            cursor.execute(sql, args)
            if commit:
                result = db.commit()
            if fetchone:
                result = cursor.fetchone()
            if fetchall:
                result = cursor.fetchall()
            return result

    def create_users_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE,
            full_name TEXT,
            phone TEXT,
            language TEXT
            )
            '''
        self.manager(sql, commit=True)

    def get_user_by_chat_id(self, chat_id):
        sql = '''
        SELECT * FROM users WHERE chat_id = ?
        '''
        return self.manager(sql, chat_id, fetchone=True)

    def first_register_user(self, chat_id, full_name):
        sql = '''
        INSERT INTO users(chat_id, full_name) VALUES (?,?)
        '''
        self.manager(sql, chat_id, full_name, commit=True)

    def update_user_to_finish_register(self, chat_id, phone):
        sql = '''
        UPDATE users SET phone = ?
        WHERE chat_id = ?
        '''
        self.manager(sql, phone, chat_id, commit=True)

    def set_user_language(self, chat_id, lang):
        user = self.get_user_by_chat_id(chat_id)
        if user:
            sql = '''
            UPDATE users SET language = ? WHERE chat_id = ?
            '''
            self.manager(sql, lang, chat_id, commit=True)
        else:
            sql = '''
            INSERT INTO users (chat_id, language) VALUES (?,?)
            '''
            self.manager(sql, chat_id, lang, commit=True)

    def get_user_language(self, chat_id):
        sql = '''
        SELECT language FROM users WHERE chat_id = ?
        '''
        result = self.manager(sql, chat_id, fetchone=True)
        if result:
            return result[0]
        return None

    def create_polls_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS polls(
        polls_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        options TEXT,
        is_active INTEGER DEFAULT 1,
        chat_id INTEGER REFERENCES users(chat_id)
        )
        '''
        self.manager(sql, commit=True)

    def create_answers_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS answers(
        answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id  INTEGER REFERENCES polls(polls_id),
        selected_option TEXT,
        chat_id INTEGER REFERENCES users(chat_id)
        )
        '''
        self.manager(sql, commit=True)

    def get_question_and_options(self, chat_id, question, options):
        sql = '''
        INSERT INTO polls (chat_id, question, options) VALUES (?,?,?)
        '''
        options_str = ",".join(options) if options else ""
        self.manager(sql, chat_id, question, options_str, commit=True)

    def show_polls(self, chat_id):
        sql = '''
        SELECT question, options FROM polls
        WHERE chat_id = ?
        '''
        return self.manager(sql, chat_id, fetchall=True)

    def deactivate_polls(self, chat_id, is_active):
        sql = '''
        UPDATE polls SET is_active = ? WHERE chat_id = ?
        '''
        self.manager(sql, is_active, chat_id, commit=True)

    def get_active_polls(self):
        sql = '''
        SELECT polls_id, question FROM polls WHERE is_active = 1
        '''
        return dict(self.manager(sql, fetchall=True))

    def get_poll_data(self, poll_id):
        sql = '''
        SELECT question, options FROM polls WHERE polls_id = ?
        '''
        result = self.manager(sql, poll_id, fetchone=True)
        if result:
            question, options_str = result
            options = options_str.split(',')
            return {'question': question, 'options': options}
        return None

    def save_text_answer(self, chat_id, question, text_answer):
        poll_id = self.get_poll_id_by_question(question)
        sql = '''
           INSERT INTO answers (poll_id, selected_option, chat_id) VALUES (?,?,?)
           '''
        self.manager(sql, poll_id, text_answer, chat_id, commit=True)

    def get_poll_id_by_question(self, question):
        sql = '''
           SELECT polls_id FROM polls WHERE question = ?
           '''
        result = self.manager(sql, question, fetchone=True)
        if result:
            return result[0]
        return None

    def save_vote(self, poll_id, option, chat_id):
        if self.has_user_voted(poll_id, chat_id):
            sql = '''
            UPDATE answers SET selected_option = ? WHERE poll_id = ? AND chat_id = ?
            '''
        else:
            sql = '''
            INSERT INTO answers (poll_id, selected_option, chat_id) VALUES (?,?,?)
            '''
        self.manager(sql, option, poll_id, chat_id, commit=True)

    def has_user_voted(self, poll_id, chat_id):
        sql = '''
        SELECT 1 FROM answers WHERE poll_id = ? AND chat_id = ?
        '''
        return self.manager(sql, poll_id, chat_id, fetchone=True) is not None

    def get_votes(self, poll_id):
        sql = '''
        SELECT selected_option FROM answers WHERE poll_id = ?
        '''
        return [row[0] for row in self.manager(sql, poll_id, fetchall=True)]

    def get_quantity_of_users(self, chat_id):
        sql = '''
        SELECT user_id FROM users
        WHERE chat_id = ?
        '''
        return self.manager(sql, chat_id, fetchall=True)

    def get_quantity_of_polls(self, chat_id):
        sql = '''
        SELECT polls_id FROM polls
        WHERE chat_id = ?
        '''
        return self.manager(sql, chat_id, fetchall=True)

    def get_quantity_of_delete_polls(self, chat_id):
        sql = '''
        SELECT polls_id FROM polls
        WHERE is_active = 0 AND chat_id = ?
        '''
        return self.manager(sql, chat_id, fetchall=True)
