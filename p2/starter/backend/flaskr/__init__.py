import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func, select
from flask_cors import CORS, cross_origin

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def pagination(questions, page):
    start = QUESTIONS_PER_PAGE * (page - 1)
    end = start + QUESTIONS_PER_PAGE

    return [question.format()
            for question in questions[start:end]]


def joinedPagination(questions, page):
    start = QUESTIONS_PER_PAGE * (page - 1)
    end = start + QUESTIONS_PER_PAGE

    return [question.Question.format()
            for question in questions[start:end]]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  @TODO: Set up CORS. Allow '*' for origins.
  '''
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response
    '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
    @app.route('/categories')
    def getCategories():
        categories = Category.query.all()
        categoriesJson = [category.format() for category in categories]

        if (len(categoriesJson) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'data': categoriesJson,
            'total': len(categoriesJson)
        })

    '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination
  at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
    @app.route('/questions')
    def getQuestions():
        questions = Question.query.all()
        page = request.args.get('page', 1, type=int)

        questionsJson = pagination(questions, page)

        if (len(questionsJson) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'data': questionsJson,
            'total': len(questions)
        })

    '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question,
  the question will be removed.
  This removal will persist in
  the database and when you refresh the page.
  '''
    @app.route('/questions/<int:questionId>', methods=['DELETE'])
    def deleteQuestion(questionId):
        question = Question.query.filter(
            Question.id == questionId).one_or_none()

        if question is None:
            abort(422)

        question.delete()

        return jsonify({
            'success': True,
            'data': questionId
        })
    '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''

    @app.route('/questions', methods=['POST'])
    def createQuestion():
        try:
            questionJson = request.get_json()

            question = Question(
                question=questionJson.get('question', None),
                answer=questionJson.get('answer', None),
                category=questionJson.get('category', None),
                difficulty=questionJson.get('difficulty', None)
            )

            question.insert()

            return jsonify({
                'success': True,
                'data': question.id
            })
        except Exception as error:
            print(error)
            abort(422)

    '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''

    @app.route('/questions/searches', methods=['POST'])
    def searchQuestions():
        questionJson = request.get_json()
        searchTerm = questionJson.get('searchTerm', None)
        questions = Question.query.filter(
            Question.question.ilike('%' + searchTerm + '%')).all()

        page = request.args.get('page', 1, type=int)

        questionsJson = pagination(questions, page)

        if (len(questionsJson) == 0):
            abort(404)

        else:
            return jsonify({
                'success': True,
                'data': questionsJson,
                'total': len(questions)
            })

    '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
    @app.route('/categories/<int:categoryId>/questions')
    def getQuestionsByCategory(categoryId):
        questions = db.session.query(
            Question,
            Category).join(
            Category,
            Question.category == Category.type).filter(
            Category.id == categoryId).all()

        page = request.args.get('page', 1, type=int)

        questionsJson = joinedPagination(questions, page)

        if (len(questionsJson) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'data': questionsJson,
            'total': len(questions)
        })

    '''
  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''

    @app.route('/questions/quizzes', methods=['POST'])
    def getQuiz():
        questionJson = request.get_json()
        previousQuestionIds = questionJson.get('previousQuestionIds', None)
        category = questionJson.get('category', None)

        categories = Category.query.all()
        categoriesNames = [category.type for category in categories]
        categoriesNames.append(None)

        if (category not in categoriesNames):
            abort(422)

        query = Question.query.order_by(func.random())

        if category is None:
            question = query.filter(
                Question.id.notin_(previousQuestionIds)).first()
        else:
            question = query.filter(
                Question.category == category,
                Question.id.notin_(previousQuestionIds)).first()

        if question is not None:
            questionJson = question.format()
        else:
            questionJson = None

        return jsonify({
            'success': True,
            'data': questionJson
        })
    '''
  @TODO:
  Create error handlers for all expected errors
  including 404 and 422.
  '''

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable request"
        }), 422

    return app
