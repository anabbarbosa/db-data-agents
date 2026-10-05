$(function() {
const chatContainer = $('#chatbox');
const messageInput = $('#textInput');
const sendBtn = $('#sendBtn');
const welcomeScreen = $('#welcomeScreen');
const newChatBtn = $('#newChatBtn');
const logoutBtn = $('#logoutBtn');
const settingsBtn = $('#settingsBtn');
const settingsBtnInline = $('#settingsBtnInline');
const settingsDropdown = $('#settingsDropdown');
const teachingModeToggle = $('#teachingModeToggle');

messageInput.on('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

messageInput.on('focus', function() {
    settingsBtnInline.addClass('active');
    sendBtn.addClass('active');
});

messageInput.on('blur', function() {
    settingsBtnInline.removeClass('active');
    sendBtn.removeClass('active');
});

messageInput.on('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        getBotResponse();
    }
});

sendBtn.on('click', getBotResponse);

function getBotResponse() {
    var rawText = messageInput.val().trim();
    
    if (rawText === '') return;
    
    if (welcomeScreen.css('display') !== 'none') {
        welcomeScreen.hide();
    }
    
    var userHtml = '<div class="message user">' +
                   '<div class="avatar user">U</div>' +
                   '<div class="message-content"><span>' + escapeHtml(rawText) + '</span></div>' +
                   '</div>';
    
    chatContainer.append(userHtml);
    
    messageInput.val('');
    messageInput.css('height', 'auto');
    
    messageInput.prop('disabled', true);
    sendBtn.prop('disabled', true);
    
    scrollToBottom();
    
    showTypingIndicator();
    
    var teachingMode = teachingModeToggle.is(':checked') ? 1 : 0;
    
    $.get("/get", { msg: rawText, teaching_mode: teachingMode })
        .done(function(data) {
            removeTypingIndicator();
            
            var explanation = (data && data.explanation) ? data.explanation : "Sem resposta.";
            var sql = (data && data.sql) ? data.sql : "";
            var qexp = (data && (data["query-explanation"] || data.query_explanation)) ? 
                      (data["query-explanation"] || data.query_explanation) : "";
            var qstatus = (data && data["query-execution-status"]) ? data["query-execution-status"] : "";
            var preview = (data && data.preview) ? data.preview : {};
            
            var sqlText = (sql || '').trim();
            var sqlLower = sqlText.toLowerCase();
            var NO_SQL_PATTERNS = [
                'não envolve uma consulta',
                'sql é inválido',
                'nao envolve uma consulta', 
                'sql is invalid',
                'does not involve a query'
            ];
            var isSqlInvalidMsg = !sqlText || NO_SQL_PATTERNS.some(function(p){ return sqlLower.indexOf(p) !== -1; });

            var botHtml = '<div class="message ai">' +
                         '<img src="/static/images/2.png" alt="AI" class="ai-avatar" />' +
                         '<div class="message-content">' +
                         '<span>' + escapeHtml(explanation) + '</span>';

    
            if (sqlText && !isSqlInvalidMsg) {
                botHtml += '</br><b>Consulta SQL:</b>' +
                          '<div class="sql-block">' + escapeHtml(sqlText) + '</div>';
            }

            var detailsId = 'details-' + Date.now() + '-' + Math.floor(Math.random() * 10000);
            var previewHtml = buildPreviewTable(preview);
            var teachingModeActive = teachingModeToggle.is(':checked');
            var hasAnyDetail = (isSqlInvalidMsg ? sqlText : '') || (teachingModeActive ? qexp : '') || qstatus || previewHtml;
            if (hasAnyDetail) {
                botHtml += '<div class="details-box">' +
                           '<div class="details-header" data-target="' + detailsId + '">' +
                           '<div class="details-title">Mais detalhes</div>' +
                           '<div class="details-chevron"></div>' +
                           '</div>' +
                           '<div class="details-content" id="' + detailsId + '">';

                if (isSqlInvalidMsg && sqlText) {
                    botHtml += '<div class="details-row">' +
                               '<b>Consulta SQL:</b>' +
                               '<div class="sql-block">' + escapeHtml(sqlText) + '</div>' +
                               '</div>';
                }
                if (teachingModeActive && qexp) {
                    botHtml += '<div class="details-row">' +
                               '<b>Explicação da Consulta:</b>' +
                               '<div>' + escapeHtml(qexp) + '</div>' +
                               '</div>';
                }
                if (qstatus) {
                    botHtml += '<div class="details-row">' +
                               '<b>Status de execução:</b>' +
                               '<div>' + escapeHtml(qstatus) + '</div>' +
                               '</div>';
                }
                if (previewHtml) {
                    botHtml += '<div class="details-row">' +
                               '<b>Pré-visualização:</b>' + previewHtml +
                               '</div>';
                }

                botHtml += '</div></div>';
            }

            botHtml += '</div></div>';
            
            chatContainer.append(botHtml);

            chatContainer.find('.details-header').off('click').on('click', function() {
                var targetId = $(this).data('target');
                var content = $('#' + targetId);
                var chev = $(this).find('.details-chevron');
                if (content.is(':visible')) {
                    content.slideUp(120);
                    chev.removeClass('rotated');
                } else {
                    content.slideDown(120);
                    chev.addClass('rotated');
                }
            });
            scrollToBottom();
            
            messageInput.prop('disabled', false);
            sendBtn.prop('disabled', false);
            messageInput.focus();
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            removeTypingIndicator();
            
            var errorMsg = 'Erro ao conectar ao backend. Certifique-se de que o Flask está rodando em http://localhost:5000';
            
            var botHtml = '<div class="message ai">' +
                         '<img src="/static/images/2.png" alt="AI" class="ai-avatar" />' +
                         '<div class="message-content error-message">' +
                         '<span>' + errorMsg + '</span>' +
                         '</div></div>';
            
            chatContainer.append(botHtml);
            scrollToBottom();
            
            messageInput.prop('disabled', false);
            sendBtn.prop('disabled', false);
            messageInput.focus();
        });
}

function buildPreviewTable(preview) {
    if (!preview) return '';
    
    var rows = null;
    
    if (preview.data && preview.data.length) {
        rows = preview.data;
    } else if (preview.amostra_primeiras_10_linhas && preview.amostra_primeiras_10_linhas.length) {
        rows = preview.amostra_primeiras_10_linhas;
    } else if (preview.message) {
        return '<div>' + escapeHtml(preview.message) + '</div>';
    }
    
    if (!rows || !rows.length) return '';
    
    var headers = Object.keys(rows[0] || {});
    if (!headers.length) return '';
    
    var thead = '<thead><tr>' + 
                headers.map(function(h) { 
                    return '<th>' + escapeHtml(h) + '</th>'; 
                }).join('') + 
                '</tr></thead>';
    
    var tbody = '<tbody>' + 
                rows.map(function(row) {
                    return '<tr>' + 
                           headers.map(function(h) { 
                               var value = row[h];
                               return '<td>' + escapeHtml(value == null ? '' : String(value)) + '</td>'; 
                           }).join('') + 
                           '</tr>';
                }).join('') + 
                '</tbody>';
    
    return '<div style="overflow-x: auto;"><table class="preview-table">' + thead + tbody + '</table></div>';
}

function showTypingIndicator() {
    var typingHtml = '<div class="message ai" id="typingIndicator">' +
                    '<img src="/static/images/2.png" alt="AI" class="ai-avatar" />' +
                    '<div class="message-content">' +
                    '<div class="typing-indicator">' +
                    '<div class="typing-dot"></div>' +
                    '<div class="typing-dot"></div>' +
                    '<div class="typing-dot"></div>' +
                    '</div></div></div>';
    
    chatContainer.append(typingHtml);
    scrollToBottom();
}

function removeTypingIndicator() {
    $('#typingIndicator').remove();
}

function scrollToBottom() {
    chatContainer[0].scrollTo({
        top: chatContainer[0].scrollHeight,
        behavior: 'smooth'
    });
}

function escapeHtml(text) {
    if (text == null) return '';
    return $('<div/>').text(String(text)).html();
}
                   
newChatBtn.on('click', function() {
    if (confirm('Deseja iniciar uma nova conversa? As mensagens atuais serão perdidas.')) {
        chatContainer.html('<div class="message ai">' +
                          '<div class="avatar ai">AI</div>' +
                          '<div class="message-content">' +
                          '<span>Olá! Sou seu assistente de dados</span>' +
                          '</div></div>');
        
        messageInput.val('');
        messageInput.css('height', 'auto');
        messageInput.focus();
    }
});

settingsBtn.on('click', function(e) {
    e.stopPropagation();
    settingsDropdown.toggleClass('show');
});

settingsBtnInline.on('click', function(e) {
    e.stopPropagation();
    settingsDropdown.toggleClass('show');
});

$(document).on('click', function(e) {
    if (!$(e.target).closest('.settings-menu').length && !$(e.target).closest('.settings-btn-inline').length) {
        settingsDropdown.removeClass('show');
    }
});

teachingModeToggle.on('change', function(e) {
    e.stopPropagation();
    var isEnabled = $(this).is(':checked');
    console.log('Teaching mode:', isEnabled ? 'enabled' : 'disabled');
    settingsDropdown.addClass('show');
});

// Logout functionality
logoutBtn.on('click', function() {
    if (confirm('Deseja fazer logout?')) {
        window.location.href = '/logout';
    }
});

messageInput.focus();
});