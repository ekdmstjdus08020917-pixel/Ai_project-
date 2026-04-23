/**
 * 필수 패키지 설치 명령어:
 * npm install express multer axios cors form-data
 */

const express = require('express');
const multer = require('multer');
const axios = require('axios');
const cors = require('cors');
const FormData = require('form-data');
const path = require('path');

const app = express();
const port = 3000;

// 미들웨어 설정
app.use(cors());
app.use(express.json());
app.use(express.static('public')); // 정적 파일 서비스

// Multer 설정 (이미지 메모리 저장)
const upload = multer({ storage: multer.memoryStorage() });

/**
 * AI 분석 API 프록시 라우트
 * 클라이언트의 요청을 받아 FastAPI 서버(8000번 포트)로 전달합니다.
 */
app.post('/proxy-analyze', upload.single('file'), async (req, res) => {
    try {
        const { prompt } = req.body;
        const file = req.file;

        if (!file) {
            return res.status(400).json({ success: false, message: "이미지 파일이 없습니다." });
        }

        // FastAPI 서버로 보낼 FormData 생성
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('file', file.buffer, {
            filename: file.originalname,
            contentType: file.mimetype,
        });

        // FastAPI 서버 호출 (8000번 포트)
        const response = await axios.post('http://localhost:8000/analyze', formData, {
            headers: {
                ...formData.getHeaders(),
            },
        });

        // 결과 반환
        res.json(response.data);
    } catch (error) {
        console.error("FastAPI 서버 연결 에러:", error.message);
        res.status(500).json({ 
            success: false, 
            message: "AI 분석 서버(FastAPI)와 통신 중 에러가 발생했습니다." 
        });
    }
});

app.listen(port, () => {
    console.log(`서버가 구동되었습니다: http://localhost:${port}`);
});
