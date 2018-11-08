import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml_tooling.result import CVResult, Result, ResultGroup


class TestResult:
    @pytest.mark.parametrize('cv', ['with_cv', 'without_cv'])
    def test_linear_model_returns_a_result(self, regression, regression_cv, cv):
        if cv == 'with_cv':
            result = regression_cv.result
            assert isinstance(result, CVResult)
            assert 2 == len(result.cross_val_scores)
            assert 2 == result.cv
            assert '2-fold Cross-validated' in result.__repr__()
            assert result.model == regression_cv.model
        else:
            result = regression.result
            assert isinstance(result, Result)
            assert hasattr(result, 'cross_val_std') is False
            assert result.model == regression.model

        assert isinstance(result.score, float)
        assert 'r2' == result.metric
        assert 'LinearRegression' == result.model_name

    @pytest.mark.parametrize('cv', ['with_cv', 'without_cv'])
    def test_regression_model_returns_a_result(self, classifier, classifier_cv, cv):
        if cv == 'with_cv':
            result = classifier_cv.result
            assert isinstance(result, CVResult)
            assert 2 == len(result.cross_val_scores)
            assert 2 == result.cv
            assert '2-fold Cross-validated' in result.__repr__()
            assert result.model == classifier_cv.model

        else:
            result = classifier.result
            assert isinstance(result, Result)
            assert hasattr(result, 'cross_val_std') is False
            assert result.model == classifier.model

        assert result.score > 0
        assert 'accuracy' == result.metric
        assert 'LogisticRegression' == result.model_name

    def test_pipeline_regression_returns_correct_result(self, base, pipeline_linear):
        model = base(pipeline_linear)
        result = model.score_model()
        assert isinstance(result, Result)
        assert 'LinearRegression' == result.model_name
        assert isinstance(result.model, Pipeline)

    def test_pipeline_logistic_returns_correct_result(self, base, pipeline_logistic):
        model = base(pipeline_logistic)
        result = model.score_model()
        assert isinstance(result, Result)
        assert 'LogisticRegression' == result.model_name
        assert isinstance(result.model, Pipeline)

    def test_cvresult_equality_operators(self):
        first_result = CVResult(model=RandomForestClassifier(), cross_val_scores=[2, 2])
        second_result = CVResult(model=RandomForestClassifier(), cross_val_scores=[1, 1])

        assert first_result > second_result

    def test_result_equality_operators(self):
        first_result = Result(model=RandomForestClassifier(), score=.7)
        second_result = Result(model=RandomForestClassifier(), score=.5)

        assert first_result > second_result

    def test_max_works_with_cv_result(self):
        first_result = CVResult(model=RandomForestClassifier(), cross_val_scores=[2, 2])
        second_result = CVResult(model=RandomForestClassifier(), cross_val_scores=[1, 1])

        max_result = max([first_result, second_result])

        assert first_result is max_result

    def test_max_works_with_result(self):
        first_result = Result(model=RandomForestClassifier(), score=.7)
        second_result = Result(model=RandomForestClassifier(), score=.5)

        max_result = max([first_result, second_result])

        assert first_result is max_result

    @pytest.mark.parametrize('with_cv', [True, False])
    def test_result_params_returns_only_clf_params(self, classifier, classifier_cv, with_cv):
        if with_cv:
            model = classifier_cv

        else:
            model = classifier

        result = model.result

        assert result.model.get_params() == result.model_params

    @pytest.mark.parametrize('with_cv', [True, False])
    def test_result_params_returns_only_clf_params_in_pipeline(self,
                                                               base,
                                                               pipeline_forest_classifier,
                                                               with_cv):

        model = base(pipeline_forest_classifier)

        if with_cv:
            result = model.score_model(cv=2)

        else:
            result = model.score_model()

        expected_params = set(RandomForestClassifier().get_params())
        assert expected_params == set(result.model_params)

    @pytest.mark.parametrize('with_cv', [True, False])
    def test_result_to_dataframe_returns_correct(self, base, pipeline_forest_classifier, with_cv):
        model = base(pipeline_forest_classifier)

        if with_cv:
            result = model.score_model(cv=2)

        else:
            result = model.score_model()

        df = result.to_dataframe()
        assert 1 == len(df)
        assert 'score' in df.columns
        assert 'max_depth' in df.columns

    def test_cv_result_with_cross_val_score_returns_correct(self, base, pipeline_forest_classifier):
        model = base(pipeline_forest_classifier)
        result = model.score_model(cv=2)
        df = result.to_dataframe(cross_val_score=True)
        assert 2 == len(df)
        assert df.loc[0, 'score'] != df.loc[1, 'score']
        assert 'cv' in df.columns
        assert 'cross_val_std' in df.columns


class TestResultGroup:

    def test_result_group_proxies_correctly(self):
        result1 = Result(RandomForestClassifier(), 2)
        result2 = Result(LogisticRegression(), 1)

        group = ResultGroup([result1, result2])
        result_name = group.model_name
        assert 'RandomForestClassifier' == result_name

    def test_result_group_sorts_before_proxying(self):
        result1 = Result(RandomForestClassifier(), 2)
        result2 = Result(LogisticRegression(), 1)

        group = ResultGroup([result2, result1])
        result_name = group.model_name

        assert 'RandomForestClassifier' == result_name

    def test_result_group_to_frame_has_correct_num_rows(self):
        result1 = Result(RandomForestClassifier(), 2)
        result2 = Result(RandomForestClassifier(), 1)

        group = ResultGroup([result2, result1])
        df = group.to_dataframe()

        assert 2 == len(df)
        assert 19 == len(df.columns)

        df_no_params = group.to_dataframe(params=False)

        assert 2 == len(df_no_params)
        assert 2 == len(df_no_params.columns)

    def test_result_cv_group_to_frame_has_correct_num_rows(self):
        result1 = CVResult(RandomForestClassifier(), cv=2, cross_val_scores=[.5, .5])
        result2 = CVResult(RandomForestClassifier(), cv=2, cross_val_scores=[.6, .6])

        group = ResultGroup([result1, result2])
        df = group.to_dataframe()

        assert 2 == len(df)
        assert 21 == len(df.columns)

        df_no_params = group.to_dataframe(params=False)

        assert 2 == len(df_no_params)
        assert 4 == len(df_no_params.columns)

    def test_result_cv_group_implements_len_properly(self):
        result1 = CVResult(RandomForestClassifier(), cv=2, cross_val_scores=[.5, .5])
        result2 = CVResult(RandomForestClassifier(), cv=2, cross_val_scores=[.6, .6])

        group = ResultGroup([result1, result2])
        assert 2 == len(group)

    def test_result_group_implements_mean_correctly(self):
        result1 = Result(RandomForestClassifier(), 2)
        result2 = Result(RandomForestClassifier(), 1)

        group = ResultGroup([result1, result2])
        assert 1.5 == group.mean_score()

    def test_result_group_implements_indexing_properly(self):
        result1 = Result(RandomForestClassifier(), 2)
        result2 = Result(RandomForestClassifier(), 1)

        group = ResultGroup([result1, result2])
        first = group[0]

        assert 2 == first.score

    def test_result_group_dir_call_includes_correct_methods(self):
        result1 = Result(RandomForestClassifier(), 2)
        result2 = Result(RandomForestClassifier(), 1)

        group = ResultGroup([result1, result2])
        options_list = dir(group)

        assert 'to_dataframe' in options_list
        assert 'plot' in options_list
        assert 'model_params' in options_list
