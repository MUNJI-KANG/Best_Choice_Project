document.addEventListener('DOMContentLoaded', function () {

    const editorElement = document.querySelector('#editor');
    const form = document.querySelector("form");

    if (!editorElement || !form) return;

    window.editorInstance = new toastui.Editor({
        el: editorElement,
        height: '600px',
        initialEditType: 'wysiwyg',
        previewStyle: 'vertical',
        initialValue: window.initialContent || ""
    });

});