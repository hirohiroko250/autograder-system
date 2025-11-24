// テスト定義画面の改善用JavaScript
(function($) {
    'use strict';

    // ページ読み込み完了時に実行
    $(document).ready(function() {
        initTestDefinitionEnhancements();
    });

    function initTestDefinitionEnhancements() {
        // 大問の満点計算機能
        addScoreCalculation();
        
        // 大問追加ボタンの改善
        enhanceQuestionGroupInlines();
        
        // バリデーション機能
        addValidation();
        
        // 学年別科目選択機能
        addGradeBasedSubjectSelection();
        
        // 大問セクションの強調表示
        highlightQuestionGroupSection();
        
        // テンプレート機能の追加
        addQuestionGroupTemplate();
    }

    function addScoreCalculation() {
        // 大問の満点入力フィールドを監視
        $(document).on('change', '.field-max_score input', function() {
            calculateTotalScore();
        });
        
        // 初回計算
        calculateTotalScore();
    }

    function calculateTotalScore() {
        var totalScore = 0;
        var hasValues = false;
        
        // 全ての大問の満点を合計
        $('.field-max_score input').each(function() {
            var value = parseInt($(this).val()) || 0;
            if (value > 0) {
                totalScore += value;
                hasValues = true;
            }
        });
        
        // テスト全体の満点フィールドを更新
        if (hasValues) {
            $('#id_max_score').val(totalScore);
            
            // 視覚的フィードバック
            $('#id_max_score').css('background-color', '#e7f3ff');
            setTimeout(function() {
                $('#id_max_score').css('background-color', '');
            }, 1000);
        }
    }

    function enhanceQuestionGroupInlines() {
        // 大問追加時のヘルプテキストを動的に更新
        $(document).on('click', '.add-row a', function() {
            setTimeout(function() {
                updateGroupNumbers();
            }, 100);
        });
        
        // 初回実行
        updateGroupNumbers();
    }

    function updateGroupNumbers() {
        $('.dynamic-questiongroup_set').each(function(index) {
            var groupNumberField = $(this).find('.field-group_number input');
            if (!groupNumberField.val()) {
                groupNumberField.val(index + 1);
            }
            
            // ヘルプテキストを更新
            var helpText = $(this).find('.field-group_number .help');
            if (helpText.length === 0) {
                $(this).find('.field-group_number').append(
                    '<div class="help">大問' + (index + 1) + 'として設定されます</div>'
                );
            }
        });
    }

    function addValidation() {
        // フォーム送信時のバリデーション
        $('form').on('submit', function(e) {
            var isValid = true;
            var errors = [];
            
            // 大問番号の重複チェック
            var groupNumbers = [];
            $('.field-group_number input').each(function() {
                var num = parseInt($(this).val());
                if (num && groupNumbers.includes(num)) {
                    errors.push('大問番号が重複しています: ' + num);
                    isValid = false;
                } else if (num) {
                    groupNumbers.push(num);
                }
            });
            
            // 満点のチェック
            $('.field-max_score input').each(function() {
                var score = parseInt($(this).val());
                if (score && score <= 0) {
                    errors.push('満点は1点以上である必要があります');
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('入力エラー:\n' + errors.join('\n'));
            }
        });
    }

    function highlightQuestionGroupSection() {
        // 大問セクションがない場合、注意メッセージを表示
        setTimeout(function() {
            var questionGroupSection = $('#questiongroup_set-group');
            if (questionGroupSection.length === 0) {
                // 大問セクションが見つからない場合、追加
                var formElement = $('form[method="post"]');
                if (formElement.length) {
                    formElement.append(
                        '<div id="questiongroup_set-group" style="border: 3px solid #dc3545; background: #fff5f5; padding: 20px; margin: 20px 0; border-radius: 10px;">' +
                        '<h2 style="background: #dc3545; color: white; padding: 15px; margin: -20px -20px 20px -20px; border-radius: 7px 7px 0 0; text-align: center;">⚠️ 大問設定が必要です ⚠️</h2>' +
                        '<p style="color: #721c24; font-size: 16px; text-align: center; margin-bottom: 15px;">このテストを有効にするには、大問設定を追加してください。</p>' +
                        '<p style="color: #721c24; text-align: center;">管理画面でテストを保存後、大問設定セクションが表示されます。</p>' +
                        '</div>'
                    );
                }
            } else {
                // 大問セクションが存在する場合、内容をチェック
                var existingQuestionGroups = $('.dynamic-questiongroup_set');
                if (existingQuestionGroups.length === 0) {
                    // 空の大問セクションにメッセージを追加
                    questionGroupSection.prepend(
                        '<div class="no-questions-notice" style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin-bottom: 15px; border-radius: 5px; text-align: center;">' +
                        '<strong>📝 大問を追加してください</strong><br>' +
                        '<small>下の「大問をもう1個追加」ボタンをクリックして大問を設定してください。</small>' +
                        '</div>'
                    );
                }
            }
        }, 500);
    }

    // 大問テンプレート機能
    function addQuestionGroupTemplate() {
        setTimeout(function() {
            var questionGroupSection = $('#questiongroup_set-group');
            if (questionGroupSection.length && $('.question-group-templates').length === 0) {
                questionGroupSection.prepend(
                    '<div class="question-group-templates" style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 8px; border: 2px solid #2196f3;">' +
                    '<h3 style="color: #1565c0; margin-bottom: 15px; text-align: center;">🎯 テンプレートから簡単作成</h3>' +
                    '<div style="text-align: center;">' +
                    '<button type="button" class="btn-template" data-template="japanese_elementary">小学生国語</button> ' +
                    '<button type="button" class="btn-template" data-template="math_elementary">小学生算数</button> ' +
                    '<button type="button" class="btn-template" data-template="english_middle">中学生英語</button> ' +
                    '<button type="button" class="btn-template" data-template="math_middle">中学生数学</button>' +
                    '</div>' +
                    '<p style="text-align: center; margin-top: 10px; color: #666; font-size: 12px;">テンプレートを選択すると、標準的な大問構成が自動設定されます</p>' +
                    '</div>'
                );
            }
        }, 600);
        
        // テンプレートボタンのクリックイベント
        $(document).on('click', '.btn-template', function() {
            var template = $(this).data('template');
            applyTemplate(template);
        });
    }

    function applyTemplate(template) {
        var templates = {
            japanese_elementary: [
                { number: 1, title: '漢字の読み取り', score: 15 },
                { number: 2, title: '漢字の書き取り', score: 15 },
                { number: 3, title: '文章題', score: 50 },
                { number: 4, title: '文章題2', score: 20 }
            ],
            math_elementary: [
                { number: 1, title: '計算', score: 20 },
                { number: 2, title: '数の問題', score: 30 },
                { number: 3, title: '図形・時間', score: 20 },
                { number: 4, title: '文章題', score: 30 }
            ],
            english_middle: [
                { number: 1, title: 'リスニング', score: 25 },
                { number: 2, title: '語彙・文法', score: 25 },
                { number: 3, title: '読解', score: 30 },
                { number: 4, title: 'ライティング', score: 20 }
            ],
            math_middle: [
                { number: 1, title: '計算', score: 25 },
                { number: 2, title: '方程式', score: 25 },
                { number: 3, title: '図形', score: 25 },
                { number: 4, title: '関数・確率', score: 25 }
            ]
        };
        
        var templateData = templates[template];
        if (!templateData) return;
        
        // 既存の大問をクリア
        $('.dynamic-questiongroup_set').each(function() {
            $(this).find('.delete input').prop('checked', true);
            $(this).hide();
        });
        
        // テンプレートの大問を追加
        templateData.forEach(function(item, index) {
            // 新しい行を追加
            $('.add-row a').click();
            
            setTimeout(function() {
                var newRow = $('.dynamic-questiongroup_set').last();
                newRow.find('.field-group_number input').val(item.number);
                newRow.find('.field-title input').val(item.title);
                newRow.find('.field-max_score input').val(item.score);
            }, 100);
        });
        
        // 合計点を再計算
        setTimeout(calculateTotalScore, 200);
    }

    function addGradeBasedSubjectSelection() {
        // 学年選択に基づく科目フィルタリング
        var gradeField = $('#id_grade_level');
        var subjectField = $('#id_subject');
        
        if (gradeField.length && subjectField.length) {
            // 科目選択肢の定義
            var subjectOptions = {
                'elementary': [
                    ['japanese', '国語'],
                    ['math', '算数']
                ],
                'middle_school': [
                    ['english', '英語'],
                    ['mathematics', '数学']
                ]
            };
            
            // 学年変更時の処理
            gradeField.on('change', function() {
                var selectedGrade = $(this).val();
                var currentSubject = subjectField.val();
                
                // 科目選択肢をクリア
                subjectField.empty();
                subjectField.append('<option value="">---------</option>');
                
                // 選択された学年に応じた科目選択肢を追加
                if (selectedGrade && subjectOptions[selectedGrade]) {
                    $.each(subjectOptions[selectedGrade], function(index, option) {
                        var selected = (option[0] === currentSubject) ? 'selected' : '';
                        subjectField.append('<option value="' + option[0] + '" ' + selected + '>' + option[1] + '</option>');
                    });
                } else {
                    // 全ての科目を表示
                    var allOptions = [].concat(subjectOptions.elementary, subjectOptions.middle_school);
                    $.each(allOptions, function(index, option) {
                        var selected = (option[0] === currentSubject) ? 'selected' : '';
                        subjectField.append('<option value="' + option[0] + '" ' + selected + '>' + option[1] + '</option>');
                    });
                }
            });
            
            // 初期化時に実行
            gradeField.trigger('change');
        }
    }

})(django.jQuery);