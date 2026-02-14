// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

var explainId = 0;
// var backendUrl = "http://114.132.79.7/";
var backendUrl = "";
//光标选中的单词/短语，用于去重
var selectText = "";
// 编辑模式标志
var isEditMode = false;
// 原始文本保存
var originalText = "";
// 标记是否已初始化编辑功能
var isEditFunctionsInitialized = false;

chrome.storage.session.get('lastWord', ({ lastWord }) => {
  updateDefinition(lastWord);
});

// 初始化：从 Chrome 存储中获取并设置下拉框的值
chrome.storage.local.get('backEndIP', function(result) {
  if (result.backEndIP) {
    backendUrl = result.backEndIP;
  }
});


chrome.storage.session.onChanged.addListener((changes) => {
  const lastWordChange = changes['lastWord'];

  if (!lastWordChange) {
    return;
  }

  updateDefinition(lastWordChange.newValue);
});

/**
 * 格式化文本
 */
function formatText(text) {
  // 移除多余的换行符和空格
  text = text.replace(/\n\s*\n/g, '\n');
  text = text.replace(/\n/g, ' ');
  text = text.replace(/\s+/g, ' ');
  return text.trim();
}

function updateDefinition(word) {
  // If the side panel was opened manually, rather than using the context menu,
  // we might not have a word to show the definition for.
  if (!word) return;

  // Hide instructions.
  document.body.querySelector('#select-a-word').style.display = 'none';

  // 格式化文本
  const formattedText = formatText(word);
  
  // Show word and definition.
  document.body.querySelector('#definition-word').innerText = formattedText;
  originalText = formattedText; // 保存原始文本
  
  // 如果在编辑模式，更新编辑区的内容
  if (isEditMode) {
    document.getElementById('text-edit-area').value = formattedText;
  }
  
  // 显示控制按钮
  document.getElementById('control-buttons').style.display = 'flex';
  
  document.getElementById('make-card').onclick = generateCard;
  // 监听释放鼠标按钮事件
  document.addEventListener("mouseup", mouseUp, true);
  document.getElementById('words-container').innerText='';
  baidu(formattedText);
  
  // 初始化编辑功能
  initEditFunctions();
}

function getCombinedText(elementId) {
  const definitionWordElement = document.getElementById(elementId);
  let combinedText = '';

  if(definitionWordElement.innerText!=''){
    combinedText = definitionWordElement.innerText;
  }else{
      // Iterate over each child node of the definitionWordElement
    for (const child of definitionWordElement.childNodes) {
      if (child.nodeType === Node.ELEMENT_NODE) {  // Ensure the node is an element
        combinedText += child.innerText + ' ';  // Add a space between words
      }
    }
  }
  // Trim any extra space from the end
  return combinedText.trim();
}


function generateCard() {
  let sentence = getCombinedText('definition-word');
  let sentenceExplain = document.getElementById('definition-explain').value;
  let frontType = 0;
  const checkbox = document.getElementById('front-type');
  if(checkbox.checked){
    frontType = 1;
  }

  let back_cards = []
  let wordElements = document.getElementsByClassName('word-explain');
  for(const wordElement of wordElements) {
    let wordOrigin = wordElement.getElementsByTagName('p')[0].innerHTML;
    let wordExplain = wordElement.getElementsByTagName('input')[0].value;
    back_cards.push({
      content: wordOrigin,
      desc:wordExplain
    });
  }

  const data = {
    front_card:
        {
          content: sentence,
          desc: sentenceExplain,
          type: frontType
        }
    ,
    back_card: back_cards
  };

  fetch(backendUrl+'api/generate_card', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  })
      .then(response => response.json())
      .then(data => {
        alert("创建成功！");
      })
      .catch((error) => {
        console.error('Error:', error);
      });
}


function handleClick(event) {
  const word = event.target.innerText;
  const explanationContainer = document.getElementById('words-container');
  const existingDiv = document.querySelector(`.word-explain[data-word="${word}"]`);

  if (existingDiv) {
    existingDiv.remove();
  } else {
    //一行单词解释，
    const wordDiv = createElement('div','word-explain');
    wordDiv.setAttribute('data-word', word);

    //单词本体
    const wordOrigin = createElement('p','word-explain-origin', 'word-explain-origin-'+explainId);
    wordOrigin.innerText = word;

    //单词的最终意思，可输入
    const explanationInput = createElement('input','word-explain-input','word-explain-input-'+explainId);
    explanationInput.type = 'text';
    explanationInput.placeholder = 'explain';

    //单词解释
    const wordDictDiv = createElement('div','word-explain-container')
    fetchTranslation(word).then(translation => {
      //解释分行展示
      translation.split("\n").forEach((transItem) => {
         let item = createElement("p", "word-explain-item", "word-explain-item-"+explainId);
         item.innerText = transItem;
         wordDictDiv.appendChild(item);
         item.onclick = function () {
           //获取explainId
           let wordId = item.id.split("-").pop();
           //点击后，将item的innerText填到同行的input中
           let inputItem = document.getElementById('word-explain-input-'+wordId);
           inputItem.value = item.innerText;
         }
      });
      explainId++;
    });

    wordDiv.appendChild(wordOrigin);
    wordDiv.appendChild(wordDictDiv);
    wordDiv.appendChild(explanationInput);
    explanationContainer.appendChild(wordDiv);
  }
}



function fetchTranslation(word) {
  word = word.replace(",","").replace(".","")
  return fetch(backendUrl+`api/trans_word?word=${encodeURIComponent(word)}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.code === 0 && data.data) {
          return data.data.translation;  // Return the translation as a string
        } else {
          throw new Error(`Error in response: ${data.message}`);
        }
      })
      .catch(error => {
        console.error('Failed to fetch translation:', error);
        return null;  // Return null or handle error as needed
      });
}

function createElement(tag, cls, id){
  let element = document.createElement(tag);
  if(cls!==undefined){
    element.className = cls;
  }
  if(id!==undefined){
    element.id = id;
  }
  return element;
}


// 释放鼠标处理函数，用于选中单词或短语
function mouseUp() {
    var text = "";
    if (window.getSelection) {
      text = window.getSelection().toString();
    } else if (document.selection && document.selection.type != "Control") {
      text = document.selection.createRange().text;
    }
    if (text!="" && text!=selectText) {
      console.log(text);
      createWordsExplainBlock(text);
      selectText = text;
    }
}

/**
 * 创建一个单词的解释
 * @param word
 */
function createWordsExplainBlock(word){
  word = trimPunctuation(word)
  const explanationContainer = document.getElementById('words-container');
  //一行单词解释，
  const wordDiv = createElement('div','word-explain','word-explain-'+explainId);

  //单词本体
  const wordOrigin = createElement('p','word-explain-origin', 'word-explain-origin-'+explainId);
  wordOrigin.innerText = word;

  //单词的最终意思，可输入
  const explanationInput = createElement('input','word-explain-input','word-explain-input-'+explainId);

  explanationInput.type = 'text';
  explanationInput.placeholder = 'explain';
  //删除这个单词的相关操作
  const wordDictDel= createElement('button','word-explain-del');
  wordDictDel.setAttribute("explainId", explainId)
  wordDictDel.innerText = "x"
  wordDictDel.addEventListener('click', function(event) {
    // 获取当前点击的按钮
    const button = event.currentTarget;

    // 获取按钮的属性
    const id = button.getAttribute('explainId');
    const element = document.getElementById('word-explain-'+id);
    if (element) {
      element.remove(); // 删除元素
      console.log('元素已删除');
    } else {
      console.log('元素不存在');
    }
  });


  //单词解释
  const wordDictDiv = createElement('div','word-explain-container')
  fetchTranslation(word).then(translation => {
    // 检查翻译是否成功获取
    if (!translation) {
      // 翻译失败时显示提示信息
      let errorItem = createElement("p", "word-explain-item");
      errorItem.innerText = "翻译获取失败，请检查网络或后端服务";
      errorItem.style.color = "#F56C6C";
      wordDictDiv.appendChild(errorItem);
      return;
    }
    
    //解释分行展示
    translation.split("\n").forEach((transItem) => {
      let item = createElement("p", "word-explain-item", "word-explain-item-"+explainId);
      item.innerText = transItem;
      wordDictDiv.appendChild(item);
      item.onclick = function () {
        //获取explainId
        let wordId = item.id.split("-").pop();
        //点击后，将item的innerText填到同行的input中
        let inputItem = document.getElementById('word-explain-input-'+wordId);
        inputItem.value = item.innerText;
      }
    });
    explainId++;
  }).catch(error => {
    // 捕获promise错误
    console.error('Translation error:', error);
    let errorItem = createElement("p", "word-explain-item");
    errorItem.innerText = "翻译服务异常";
    errorItem.style.color = "#F56C6C";
    wordDictDiv.appendChild(errorItem);
  });


  wordDiv.appendChild(wordOrigin);
  wordDiv.appendChild(wordDictDiv);
  wordDiv.appendChild(explanationInput);
  wordDiv.appendChild(wordDictDel)
  explanationContainer.appendChild(wordDiv);
}

/**
 * 删除字符串开头和结尾的空格和标点符号
 * @param str
 * @returns {*}
 */
function trimPunctuation(str) {
  return str.replace(/^[\W_]+|[\W_]+$/g, '');
}

// ==================== 新增功能：编辑和排版 ====================

/**
 * 初始化编辑功能（只初始化一次）
 */
function initEditFunctions() {
  // 如果已经初始化过，则跳过
  if (isEditFunctionsInitialized) {
    return;
  }
  
  isEditFunctionsInitialized = true;
  
  const toggleEditBtn = document.getElementById('toggle-edit-btn');
  const retranslateBtn = document.getElementById('retranslate-btn');
  
  // 编辑按钮点击事件
  toggleEditBtn.addEventListener('click', function() {
    if (!isEditMode) {
      // 进入编辑模式
      enterEditMode();
    } else {
      // 退出编辑模式（保存并重新排版）
      exitEditMode();
    }
  });
  
  // 重新翻译按钮点击事件
  retranslateBtn.addEventListener('click', function() {
    retranslateText();
  });
}

/**
 * 进入编辑模式
 */
function enterEditMode() {
  isEditMode = true;
  const toggleEditBtn = document.getElementById('toggle-edit-btn');
  const retranslateBtn = document.getElementById('retranslate-btn');
  const textEditArea = document.getElementById('text-edit-area');
  const definitionWord = document.getElementById('definition-word');
  
  // 获取当前文本（去除按钮包装）
  const currentText = getCombinedText('definition-word');
  
  // 显示文本编辑区
  textEditArea.value = currentText;
  textEditArea.style.display = 'block';
  
  // 隐藏排版后的文本
  definitionWord.style.display = 'none';
  
  // 更改按钮文字
  toggleEditBtn.innerText = '保存排版';
  toggleEditBtn.classList.remove('edit-btn');
  toggleEditBtn.classList.add('save-btn');
  
  // 显示重新翻译按钮
  retranslateBtn.style.display = 'block';
}

/**
 * 退出编辑模式
 */
function exitEditMode() {
  isEditMode = false;
  const toggleEditBtn = document.getElementById('toggle-edit-btn');
  const retranslateBtn = document.getElementById('retranslate-btn');
  const textEditArea = document.getElementById('text-edit-area');
  const definitionWord = document.getElementById('definition-word');
  
  // 获取编辑后的文本并格式化
  const editedText = textEditArea.value.trim();
  
  if (editedText) {
    // 格式化文本（类似 article_reader 的处理）
    const formattedText = formatText(editedText);
    
    // 更新显示区域 - 使用原始的简单文本显示方式
    definitionWord.innerText = formattedText;
    
    originalText = editedText; // 更新原始文本
  }
  
  // 隐藏文本编辑区
  textEditArea.style.display = 'none';
  
  // 显示排版后的文本
  definitionWord.style.display = 'flex';
  
  // 更改按钮文字
  toggleEditBtn.innerText = '编辑文本';
  toggleEditBtn.classList.remove('save-btn');
  toggleEditBtn.classList.add('edit-btn');
  
  // 隐藏重新翻译按钮
  retranslateBtn.style.display = 'none';
}

/**
 * 重新翻译
 */
function retranslateText() {
  const textEditArea = document.getElementById('text-edit-area');
  const text = textEditArea.value.trim();
  
  if (!text) {
    alert('请先输入文本！');
    return;
  }
  
  // 退出编辑模式
  exitEditMode();
  
  // 只清空整句翻译，保留已选择的单词解释块
  document.getElementById('definition-explain').value = '';
  
  // 重新翻译
  baidu(text);
}
