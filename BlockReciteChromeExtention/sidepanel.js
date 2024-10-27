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
var backendUrl = "http://114.132.79.7/";
//光标选中的单词/短语，用于去重
var selectText = "";

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

function updateDefinition(word) {
  // If the side panel was opened manually, rather than using the context menu,
  // we might not have a word to show the definition for.
  if (!word) return;

  // Hide instructions.
  document.body.querySelector('#select-a-word').style.display = 'none';

  // Show word and definition.
  document.body.querySelector('#definition-word').innerText = word;
  document.getElementById('make-card').onclick = generateCard;
  // 监听释放鼠标按钮事件
  document.addEventListener("mouseup", mouseUp, true);
  document.getElementById('words-container').innerText='';
  baidu(word);
}

function getCombinedText(elementId) {
  const definitionWordElement = document.getElementById(elementId);
  let combinedText = '';

  // Iterate over each child node of the definitionWordElement
  for (const child of definitionWordElement.childNodes) {
    if (child.nodeType === Node.ELEMENT_NODE) {  // Ensure the node is an element
      combinedText += child.innerText + ' ';  // Add a space between words
    }
  }

  // Trim any extra space from the end
  return combinedText.trim();
}


function generateCard() {
  let sentence = getCombinedText('definition-word');
  let sentenceExplain = document.getElementById('definition-explain').value;

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
          desc: sentenceExplain
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
