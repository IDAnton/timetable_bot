import db
import keyboards
import datetime


def int_r(num):  # Округление
    num = int(num + (0.5 if num > 0 else -0.5))
    return num


def search(surname):
    surname = surname.lower().capitalize()
    tutors_list = db.get_tutors_by_surname(surname=surname)
    if not tutors_list:
        return False
    return keyboards.review_search_list(tutors_list)


def load_reviews(tutor_id):  # TODO load reviews partly
    reviews = db.get_review(tutor_id=tutor_id)
    res = []
    for review in reviews:
        res_tmp = review[7] + '\n'  # date
        surname, name, patronymic = db.get_tutor_info(tutor_id=tutor_id)['name']
        res_tmp += f'{surname} {name} {patronymic}\n'
        res_tmp += int_r(review[1]) * keyboards.REVIEW_SYMBOL + '\n\n'  # stars
        if review[2] is not None:
            res_tmp += review[2]  # text
        res.append({'text': res_tmp, 'keyboard': keyboards.like_dislike_review(review_id=review[0])})
    return res


def load_review_by_id(review_id):
    review = db.get_review_by_id(review_id=review_id)
    res = review[7] + '\n'
    surname, name, patronymic = db.get_tutor_info(tutor_id=review[5])['name']
    res += f'{surname} {name} {patronymic}\n'
    res += int_r(review[1]) * keyboards.REVIEW_SYMBOL + '\n\n'
    if review[2] is not None:
        res += review[2]
    return res


def add_review_rating(user_id, tutor_id, rating):
    if db.check_reviewed(user_id=user_id, tutor_id=tutor_id) == 'Rating':
        date = str((datetime.datetime.now() + datetime.timedelta(hours=7)).date().isoformat())
        db.add_review_rating(user_id=user_id, tutor_id=tutor_id, rating=rating, date=date)
        return True
    else:
        return False


def add_review_text(user_id, tutor_id, text):
    if db.check_reviewed(user_id=user_id, tutor_id=tutor_id) == 'Text':
        db.add_review_text(user_id=user_id, tutor_id=tutor_id, text=text)
        return True
    else:
        return False


def tutor_info(tutor_id):
    tutor = db.get_tutor_info(tutor_id=tutor_id)
    surname = tutor['name'][0]
    name = tutor['name'][1]
    p = tutor['name'][2]
    amount = tutor['amount']
    rating = tutor['rating']
    if amount != 0:
        res = f'{surname} {name} {p}\n{keyboards.REVIEW_SYMBOL * int(rating)}\n{round(rating, 1)} / 5\nОтзывов: {amount}'
    else:
        res = f'{surname} {name} {p}\nОтзывов пока нет, оставь первый!'
    return res


def like_review(user_id, review_id, like_type):
    answered = db.check_if_liked(user_id=user_id, review_id=review_id)
    if not answered:
        if like_type == 'l':
            db.set_review_like(user_id=user_id, review_id=review_id, like_type=True)
            return '👍'
        if like_type == 'd':
            db.set_review_like(user_id=user_id, review_id=review_id, like_type=False)
            return '👎'
    else:
        if answered == 'l':
            return 'Ты уже поставил 👍'
        if answered == 'd':
            return 'Ты уже поставил 👎'


if __name__ == '__main__':
    print(add_review_text(user_id=383582494, tutor_id=2000, text='test'))
