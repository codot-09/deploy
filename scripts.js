// DOM Elements
const playBtn = document.getElementById('play-btn');
const gameSelection = document.getElementById('game-selection');
const ticTacToeBtn = document.getElementById('tic-tac-toe-btn');
const memoryGameBtn = document.getElementById('memory-game-btn');
const startPage = document.getElementById('start-page');
const ticTacToe = document.getElementById('tic-tac-toe');
const memoryGame = document.getElementById('memory-game');
const backToMenuTTT = document.getElementById('back-to-menu-ttt');
const backToMenuMemory = document.getElementById('back-to-menu-memory');
const boardTTT = document.getElementById('board');
const memoryBoard = document.getElementById('memory-board');
let timer = 0;
let timerInterval;
const timerElement = document.getElementById('timer');

// Show Game Selection Screen
playBtn.addEventListener('click', () => {
  startPage.style.display = 'none';
  gameSelection.style.display = 'block';
});

// Show Tic-Tac-Toe Game
ticTacToeBtn.addEventListener('click', () => {
  gameSelection.style.display = 'none';
  ticTacToe.style.display = 'block';
  renderTicTacToeBoard();
  startTimer();
});

// Show Memory Game
memoryGameBtn.addEventListener('click', () => {
  gameSelection.style.display = 'none';
  memoryGame.style.display = 'block';
  renderMemoryGameBoard();
  startTimer();
});

// Go Back to Menu from Tic-Tac-Toe
backToMenuTTT.addEventListener('click', () => {
  ticTacToe.style.display = 'none';
  gameSelection.style.display = 'block';
  resetGame();
});

// Go Back to Menu from Memory Game
backToMenuMemory.addEventListener('click', () => {
  memoryGame.style.display = 'none';
  gameSelection.style.display = 'block';
  resetGame();
});

function startTimer() {
    timerInterval = setInterval(() => {
      timer++;
      const minutes = Math.floor(timer / 60);
      const seconds = timer % 60;
      timerElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }, 1000);
  }

function updateTimer() {
  const timerElement = document.getElementById('timer');
  timerElement.textContent = `Time remaining: ${timeRemaining}s`;
}

// Memory Game Logic
const cards = ['A', 'B', 'C', 'D', 'A', 'B', 'C', 'D'];
let flippedCards = [];
let matchedCards = 0;

function renderMemoryGameBoard() {
  memoryBoard.innerHTML = '';
  shuffle(cards);
  cards.forEach((card, index) => {
    const cardDiv = document.createElement('div');
    cardDiv.classList.add('card');
    cardDiv.dataset.index = index;
    cardDiv.onclick = () => flipCard(cardDiv, card, index);
    memoryBoard.appendChild(cardDiv);
  });
}

function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
}

function flipCard(cardDiv, card, index) {
  if (flippedCards.length < 2 && !cardDiv.classList.contains('flipped')) {
    cardDiv.classList.add('flipped');
    cardDiv.style.backgroundColor = 'darkgoldenrod';  // Yellow color for selection
    cardDiv.textContent = card;
    flippedCards.push({ cardDiv, card, index });

    if (flippedCards.length === 2) {
      setTimeout(() => checkMatch(), 1000);
    }
  }
}

function checkMatch() {
  const [firstCard, secondCard] = flippedCards;
  if (firstCard.card === secondCard.card) {
    matchedCards += 1;
    firstCard.cardDiv.style.backgroundColor = 'darkgreen';  // Dark green for match
    secondCard.cardDiv.style.backgroundColor = 'darkgreen';
    firstCard.cardDiv.classList.add('matched');
    secondCard.cardDiv.classList.add('matched');
    if (matchedCards === cards.length / 2) {
      setTimeout(() => alert('You Win!'), 500);
      clearInterval(timer);  // Stop timer when game is won
      resetGame();
    }
  } else {
    firstCard.cardDiv.style.backgroundColor = 'darkred';  // Dark red for no match
    secondCard.cardDiv.style.backgroundColor = 'darkred';
    setTimeout(() => {
      firstCard.cardDiv.classList.remove('flipped');
      secondCard.cardDiv.classList.remove('flipped');
      firstCard.cardDiv.style.backgroundColor = '';
      secondCard.cardDiv.style.backgroundColor = '';
    }, 1000);
  }
  flippedCards = [];
}

// Tic-Tac-Toe Board Logic
let currentPlayer = 'X';
let board = ['', '', '', '', '', '', '', '', ''];
let gameOver = false;

function renderTicTacToeBoard() {
  boardTTT.innerHTML = '';
  board.forEach((cell, index) => {
    const cellDiv = document.createElement('div');
    cellDiv.classList.add('cell');
    cellDiv.textContent = cell;
    cellDiv.onclick = () => makeMove(index);
    boardTTT.appendChild(cellDiv);
  });
}

function makeMove(index) {
  if (board[index] === '' && !gameOver) {
    board[index] = currentPlayer;
    currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
    renderTicTacToeBoard();
    checkWinner();
  }
}

function checkWinner() {
  const winningCombinations = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
  ];

  for (const combination of winningCombinations) {
    const [a, b, c] = combination;
    if (board[a] && board[a] === board[b] && board[a] === board[c]) {
      alert(`${board[a]} wins!`);
      gameOver = true;
      clearInterval(timer);  // Stop timer when game is won
      resetGame();
      return;
    }
  }

  if (!board.includes('')) {
    alert("It's a draw!");
    gameOver = true;
    clearInterval(timer);  // Stop timer when game is a draw
    resetGame();
  }
}

function resetGame() {
  board = ['', '', '', '', '', '', '', '', ''];
  currentPlayer = 'X';
  gameOver = false;
  matchedCards = 0;
  flippedCards = [];
  renderTicTacToeBoard();
  renderMemoryGameBoard();
}
