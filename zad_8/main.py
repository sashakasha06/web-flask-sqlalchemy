from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Work
from forms import LoginForm
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def init_db():
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email='test@test.ru').first():
            test_user = User(
                email='test@test.ru',
                name='Test User'
            )
            test_user.set_password('Password12345')
            db.session.add(test_user)

            test_user2 = User(
                email='test2@test.ru',
                name='Test User2'
            )
            test_user2.set_password('Password54321')
            db.session.add(test_user2)

            test_user3 = User(
                email='test3@test.ru',
                name='Test User3'
            )
            test_user3.set_password('Password54')
            db.session.add(test_user3)
            db.session.flush()


            # Создаем тестовые работы
            work1 = (Work(id=1, description="Пример описания 1", user_id=test_user.id))
            work2 = (Work(id=2, description="Пример описания 2", user_id=test_user2.id))
            work3 = (Work(id=3, description="Пример описания 3", user_id=test_user2.id))
            work4 = (Work(id=4, description="Пример описания 4", user_id=test_user2.id))
            db.session.add(work1)
            db.session.add(work2)
            db.session.add(work3)
            db.session.add(work4)
            db.session.commit()


init_db()


@app.route('/')
def index():
    if current_user.is_authenticated:
        # Явно загружаем работы для текущего пользователя
        works = Work.query.filter_by(user_id=current_user.id).all()
        print(f"Найдено работ: {len(works)}")  # Для отладки
        return render_template('index.html', works=works)
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('index'))
        return render_template('login.html', form=form, message="Неверный email или пароль")
    return render_template('login.html', form=form)


@app.route('/add_work', methods=['GET', 'POST'])
@login_required
def add_work():
    if request.method == 'POST':
        description = request.form.get('description')

        # Создаём новую работу с текущим пользователем
        new_work = Work(description=description, user_id=current_user.id) # используем ID текущего пользователя

        db.session.add(new_work)
        db.session.commit()

        flash('Работа успешно добавлена!', 'success')
        return redirect(url_for('index'))


    return render_template('add_work.html')


@app.route('/edit_work/<int:work_id>', methods=['GET', 'POST'])
@login_required
def edit_work(work_id):
    work = Work.query.get_or_404(work_id)

    # Проверка прав доступа
    if not work.can_edit(current_user):
        flash('У вас нет прав для редактирования этой работы', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            work.description = request.form['description']
            db.session.commit()
            flash('Работа успешно обновлена!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении: {str(e)}', 'danger')

    # GET-запрос - показываем форму редактирования
    return render_template('edit_work.html', work=work)


@app.route('/all_works')
@login_required
def all_works():
    if current_user.id != 1:
        flash('Доступно только капитану!', 'danger')
        return redirect(url_for('index'))

    works = Work.query.order_by(Work.user_id).all()  # Сортируем по user_id для удобства
    return render_template('all_works.html', works=works)


@app.route('/delete_work/<int:work_id>', methods=['GET', 'POST'])
@login_required
def delete_work(work_id):
    work = Work.query.get_or_404(work_id)

    if current_user.id != 1:  # Только капитан может удалять
        flash('У вас нет прав для этого действия', 'danger')
        return redirect(url_for('index'))

    db.session.delete(work)
    db.session.commit()
    flash('Работа успешно удалена', 'success')
    return redirect(url_for('all_works'))
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('base'))


if __name__ == '__main__':
    app.run(debug=True)