from streamlit.testing.v1 import AppTest


def test_workspace(tmp_path,monkeypatch):
    monkeypatch.setenv("SENTINEL_DB",str(tmp_path/"ui.db"))
    monkeypatch.setenv("SENTINEL_ROWS","1800")
    app=AppTest.from_file("../app.py",default_timeout=120).run()
    assert not app.exception and app.title[0].value=="Risk overview"
    for page in app.radio(key="navigation").options[1:]:
        app.radio(key="navigation").set_value(page).run()
        assert not app.exception, page
        if page=="Risk simulator":
            app.button[-1].click().run()
            assert not app.exception and len(app.metric)==3
        if page=="Investigations":
            app.text_area[0].set_value("Synthetic case review")
            app.button[0].click().run()
            assert not app.exception and app.text_area[0].value=="Synthetic case review"
