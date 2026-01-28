---
title: "录音文件识别-Fun-ASR/Paraformer/SenseVoice-大模型服务平台百炼-阿里云"
source: "https://help.aliyun.com/zh/model-studio/recording-file-recognition"
date: "2026-01-27 22:34:36"
---

# 录音文件识别-Fun-ASR/Paraformer/SenseVoice-大模型服务平台百炼-阿里云

- Source: https://help.aliyun.com/zh/model-studio/recording-file-recognition

Fun-ASR/Paraformer /SenseVoice 的录音文件识别模型能将录制好的音频转换为文本，支持单个文件识别和批量文件识别，适用于处理不需要即时返回结果的场景。

## ** 核心功能**

- ** 多语种识别** ：支持识别中文（含多种方言）、英、日、韩、德、法、俄等多种语言。

- ** 广泛格式兼容** ：支持任意采样率，并兼容 aac、wav、mp3 等多种主流音视频格式。

- ** 长音频文件处理** ：支持对单个时长不超过 12 小时、体积不超过 2GB 的音频文件进行异步转写。

- ** 歌唱识别** ：即使在伴随背景音乐（BGM）的情况下，也能实现整首歌曲的转写（仅 fun-asr 和 fun-asr-2025-11-07 模型支持该功能）。

- ** 丰富识别功能** ：提供说话人分离、敏感词过滤、句子/词语级时间戳、热词增强等可配置功能，满足个性化需求。

## ** 适用范围**

** 支持的模型：**

## 中国内地

在[中国内地部署模式](https://help.aliyun.com/zh/model-studio/regions/#080da663a75xh) 下，接入点与数据存储均位于** 北京地域** ，模型推理计算资源仅限于中国内地。

调用以下模型时，请选择北京地域的[API Key](https://bailian.console.aliyun.com/?tab=model#/api-key) ：

- ** Fun-ASR** ：fun-asr（稳定版，当前等同 fun-asr-2025-11-07）、fun-asr-2025-11-07（快照版）、fun-asr-2025-08-25（快照版）、fun-asr-mtl（稳定版，当前等同 fun-asr-mtl-2025-08-25）、fun-asr-mtl-2025-08-25（快照版）

- ** Paraformer** ：paraformer-v2、paraformer-8k-v2、paraformer-v1、paraformer-8k-v1、paraformer-mtl-v1

- ** SenseVoice（即将下线）** ：sensevoice-v1

## 国际

在[国际部署模式](https://help.aliyun.com/zh/model-studio/regions/#080da663a75xh) 下，接入点与数据存储均位于** 新加坡地域** ，模型推理计算资源在全球范围内动态调度（不含中国内地）。

调用以下模型时，请选择新加坡地域的[API Key](https://modelstudio.console.aliyun.com/?tab=dashboard#/api-key) ：

- ** Fun-ASR** ：fun-asr（稳定版，当前等同 fun-asr-2025-11-07）、fun-asr-2025-11-07（快照版）、fun-asr-2025-08-25（快照版）、fun-asr-mtl（稳定版，当前等同 fun-asr-mtl-2025-08-25）、fun-asr-mtl-2025-08-25（快照版）

更多信息请参见[模型列表](https://help.aliyun.com/zh/model-studio/models)

## ** 模型选型**

| 场景 | 推荐模型 | 理由 |
| --- | --- | --- |
| 中文识别（会议/直播） | fun-asr | 针对中文深度优化，覆盖多种方言；远场VAD和噪声鲁棒性强，适合嘈杂或多人远距离发言的真实场景，准确率更高 |
| 多语种识别（国际会议） | fun-asr-mtl、paraformer-v2 | 一个模型即可应对多语言需求，简化开发和部署 |
| 文娱内容分析与字幕生成 | fun-asr | 具备独特的歌唱识别能力，能有效转写歌曲、直播中的演唱片段；结合其噪声鲁棒性，非常适合处理复杂的媒体音频 |
| 新闻/访谈节目字幕生成 | fun-asr、paraformer-v2 | 长音频+标点预测+时间戳，直接生成结构化字幕 |
| 智能硬件远场语音交互 | fun-asr | 远场VAD（语音活动检测）经过专门优化，能在家庭、车载等嘈杂环境下，更准确地捕捉和识别用户的远距离指令 |

更多说明请参见[模型功能特性对比](https://help.aliyun.com/zh/model-studio/recording-file-recognition#ea5edc7ae4cq7)

## ** 快速开始**

下面是调用 API 的示例代码。

 您需要已[获取API Key](https://help.aliyun.com/zh/model-studio/get-api-key) 并[配置API Key到环境变量](https://help.aliyun.com/zh/model-studio/configure-api-key-through-environment-variables) 。如果通过 SDK 调用，还需要[安装DashScope SDK](https://help.aliyun.com/zh/model-studio/install-sdk) 。

## Fun-ASR

由于音视频文件的尺寸通常较大，文件传输和语音识别处理均需要时间，文件转写 API 通过异步调用方式来提交任务。开发者需要通过查询接口，在文件转写完成后获得语音识别结果。

## Python

```python
from http import HTTPStatus
from dashscope.audio.asr import Transcription
from urllib import request
import dashscope
import os
import json

# 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

# 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

task_response = Transcription.async_call(
    model='fun-asr',
    file_urls=['https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav',
               'https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_male2.wav'],
    language_hints=['zh', 'en']  # language_hints为可选参数，用于指定待识别音频的语言代码。取值范围请参见API参考文档。
)

transcription_response = Transcription.wait(task=task_response.output.task_id)

if transcription_response.status_code == HTTPStatus.OK:
    for transcription in transcription_response.output['results']:
        if transcription['subtask_status'] == 'SUCCEEDED':
            url = transcription['transcription_url']
            result = json.loads(request.urlopen(url).read().decode('utf8'))
            print(json.dumps(result, indent=4,
                            ensure_ascii=False))
        else:
            print('transcription failed!')
            print(transcription)
else:
    print('Error: ', transcription_response.output.message)
```

## Java

```java
import com.alibaba.dashscope.audio.asr.transcription.*;
import com.alibaba.dashscope.utils.Constants;
import com.google.gson.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Arrays;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        // 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1
        Constants.baseHttpApiUrl = "https://dashscope.aliyuncs.com/api/v1";
        // 创建转写请求参数。
        TranscriptionParam param =
                TranscriptionParam.builder()
                        // 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
                        // 若没有配置环境变量，请用百炼API Key将下行替换为：.apiKey("sk-xxx")
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .model("fun-asr")
                        // language_hints为可选参数，用于指定待识别音频的语言代码。取值范围请参见API参考文档。
                        .parameter("language_hints", new String[]{"zh", "en"})
                        .fileUrls(
                                Arrays.asList(
                                        "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav",
                                        "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_male2.wav"))
                        .build();
        try {
            Transcription transcription = new Transcription();
            // 提交转写请求
            TranscriptionResult result = transcription.asyncCall(param);
            System.out.println("RequestId: " + result.getRequestId());
            // 阻塞等待任务完成并获取结果
            result = transcription.wait(
                    TranscriptionQueryParam.FromTranscriptionParam(param, result.getTaskId()));
            // 获取转写结果
            List<TranscriptionTaskResult> taskResultList = result.getResults();
            if (taskResultList != null && taskResultList.size() > 0) {
                for (TranscriptionTaskResult taskResult : taskResultList) {
                    String transcriptionUrl = taskResult.getTranscriptionUrl();
                    HttpURLConnection connection =
                            (HttpURLConnection) new URL(transcriptionUrl).openConnection();
                    connection.setRequestMethod("GET");
                    connection.connect();
                    BufferedReader reader =
                            new BufferedReader(new InputStreamReader(connection.getInputStream()));
                    Gson gson = new GsonBuilder().setPrettyPrinting().create();
                    JsonElement jsonResult = gson.fromJson(reader, JsonObject.class);
                    System.out.println(gson.toJson(jsonResult));
                }
            }
        } catch (Exception e) {
            System.out.println("error: " + e);
        }
        System.exit(0);
    }
}
```

完整的识别结果会以 JSON 格式打印在控制台。完整结果包含转换后的文本以及文本在音视频文件中的起始、结束时间（以毫秒为单位）。

- 第一个结果

```json
{
    "file_url": "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav",
    "properties": {
        "audio_format": "pcm_s16le",
        "channels": [
            0
        ],
        "original_sampling_rate": 16000,
        "original_duration_in_milliseconds": 3834
    },
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 2480,
            "text": "Hello World，这里是阿里巴巴语音实验室。",
            "sentences": [
                {
                    "begin_time": 760,
                    "end_time": 3240,
                    "text": "Hello World，这里是阿里巴巴语音实验室。",
                    "sentence_id": 1,
                    "words": [
                        {
                            "begin_time": 760,
                            "end_time": 1000,
                            "text": "Hello",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1000,
                            "end_time": 1120,
                            "text": " World",
                            "punctuation": "，"
                        },
                        {
                            "begin_time": 1400,
                            "end_time": 1920,
                            "text": "这里是",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1920,
                            "end_time": 2520,
                            "text": "阿里巴巴",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2520,
                            "end_time": 2840,
                            "text": "语音",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2840,
                            "end_time": 3240,
                            "text": "实验室",
                            "punctuation": "。"
                        }
                    ]
                }
            ]
        }
    ]
}
```

- 第二个结果

```json
{
    "file_url": "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_male2.wav",
    "properties": {
        "audio_format": "pcm_s16le",
        "channels": [
            0
        ],
        "original_sampling_rate": 16000,
        "original_duration_in_milliseconds": 4726
    },
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 3800,
            "text": "Hello World，这里是阿里巴巴语音实验室。",
            "sentences": [
                {
                    "begin_time": 680,
                    "end_time": 4480,
                    "text": "Hello World，这里是阿里巴巴语音实验室。",
                    "sentence_id": 1,
                    "words": [
                        {
                            "begin_time": 680,
                            "end_time": 960,
                            "text": "Hello",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 960,
                            "end_time": 1080,
                            "text": " World",
                            "punctuation": "，"
                        },
                        {
                            "begin_time": 1480,
                            "end_time": 2160,
                            "text": "这里是",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2160,
                            "end_time": 3080,
                            "text": "阿里巴巴",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 3080,
                            "end_time": 3520,
                            "text": "语音",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 3520,
                            "end_time": 4480,
                            "text": "实验室",
                            "punctuation": "。"
                        }
                    ]
                }
            ]
        }
    ]
}
```

## Paraformer

由于音视频文件的尺寸通常较大，文件传输和语音识别处理均需要时间，文件转写 API 通过异步调用方式来提交任务。开发者需要通过查询接口，在文件转写完成后获得语音识别结果。

## Python

```python
from http import HTTPStatus
from dashscope.audio.asr import Transcription
from urllib import request
import dashscope
import os
import json

# 获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

task_response = Transcription.async_call(
    model='paraformer-v2',
    file_urls=['https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav',
               'https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_male2.wav'],
    language_hints=['zh', 'en']  # language_hints为可选参数，用于指定待识别音频的语言代码。仅Paraformer系列的paraformer-v2模型支持该参数，取值范围请参见API参考文档。
)

transcription_response = Transcription.wait(task=task_response.output.task_id)

if transcription_response.status_code == HTTPStatus.OK:
    for transcription in transcription_response.output['results']:
        if transcription['subtask_status'] == 'SUCCEEDED':
            url = transcription['transcription_url']
            result = json.loads(request.urlopen(url).read().decode('utf8'))
            print(json.dumps(result, indent=4,
                            ensure_ascii=False))
        else:
            print('transcription failed!')
            print(transcription)
else:
    print('Error: ', transcription_response.output.message)
```

## Java

```java
import com.alibaba.dashscope.audio.asr.transcription.*;
import com.google.gson.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Arrays;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        // 创建转写请求参数
        TranscriptionParam param =
                TranscriptionParam.builder()
                        // 获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
                        // 若没有配置环境变量，请用百炼API Key将下行替换为：.apiKey("sk-xxx")
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .model("paraformer-v2")
                        // language_hints为可选参数，用于指定待识别音频的语言代码。仅Paraformer系列的paraformer-v2模型支持该参数，取值范围请参见API参考文档。
                        .parameter("language_hints", new String[]{"zh", "en"})
                        .fileUrls(
                                Arrays.asList(
                                        "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav",
                                        "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_male2.wav"))
                        .build();
        try {
            Transcription transcription = new Transcription();
            // 提交转写请求
            TranscriptionResult result = transcription.asyncCall(param);
            System.out.println("RequestId: " + result.getRequestId());
            // 阻塞等待任务完成并获取结果
            result = transcription.wait(
                    TranscriptionQueryParam.FromTranscriptionParam(param, result.getTaskId()));
            // 获取转写结果
            List<TranscriptionTaskResult> taskResultList = result.getResults();
            if (taskResultList != null && taskResultList.size() > 0) {
                for (TranscriptionTaskResult taskResult : taskResultList) {
                    String transcriptionUrl = taskResult.getTranscriptionUrl();
                    HttpURLConnection connection =
                            (HttpURLConnection) new URL(transcriptionUrl).openConnection();
                    connection.setRequestMethod("GET");
                    connection.connect();
                    BufferedReader reader =
                            new BufferedReader(new InputStreamReader(connection.getInputStream()));
                    Gson gson = new GsonBuilder().setPrettyPrinting().create();
                    JsonElement jsonResult = gson.fromJson(reader, JsonObject.class);
                    System.out.println(gson.toJson(jsonResult));
                }
            }
        } catch (Exception e) {
            System.out.println("error: " + e);
        }
        System.exit(0);
    }
}
```

完整的识别结果会以 JSON 格式打印在控制台。完整结果包含转换后的文本以及文本在音视频文件中的起始、结束时间（以毫秒为单位）。

- 第一个结果

```json
{
    "file_url": "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_male2.wav",
    "properties": {
        "audio_format": "pcm_s16le",
        "channels": [
            0
        ],
        "original_sampling_rate": 16000,
        "original_duration_in_milliseconds": 4726
    },
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 4720,
            "text": "Hello world, 这里是阿里巴巴语音实验室。",
            "sentences": [
                {
                    "begin_time": 0,
                    "end_time": 4720,
                    "text": "Hello world, 这里是阿里巴巴语音实验室。",
                    "sentence_id": 1,
                    "words": [
                        {
                            "begin_time": 0,
                            "end_time": 629,
                            "text": "Hello ",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 629,
                            "end_time": 944,
                            "text": "world",
                            "punctuation": ", "
                        },
                        {
                            "begin_time": 944,
                            "end_time": 1258,
                            "text": "这",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1258,
                            "end_time": 1573,
                            "text": "里",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1573,
                            "end_time": 1888,
                            "text": "是",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1888,
                            "end_time": 2202,
                            "text": "阿",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2202,
                            "end_time": 2517,
                            "text": "里",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2517,
                            "end_time": 2832,
                            "text": "巴",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2832,
                            "end_time": 3146,
                            "text": "巴",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 3146,
                            "end_time": 3461,
                            "text": "语",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 3461,
                            "end_time": 3776,
                            "text": "音",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 3776,
                            "end_time": 4090,
                            "text": "实",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 4090,
                            "end_time": 4405,
                            "text": "验",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 4405,
                            "end_time": 4720,
                            "text": "室",
                            "punctuation": "。"
                        }
                    ]
                }
            ]
        }
    ]
}
```

- 第二个结果

```json
{
    "file_url": "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav",
    "properties": {
        "audio_format": "pcm_s16le",
        "channels": [
            0
        ],
        "original_sampling_rate": 16000,
        "original_duration_in_milliseconds": 3834
    },
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 3720,
            "text": "Hello word, 这里是阿里巴巴语音实验室。",
            "sentences": [
                {
                    "begin_time": 100,
                    "end_time": 3820,
                    "text": "Hello word, 这里是阿里巴巴语音实验室。",
                    "sentence_id": 1,
                    "words": [
                        {
                            "begin_time": 100,
                            "end_time": 596,
                            "text": "Hello ",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 596,
                            "end_time": 844,
                            "text": "word",
                            "punctuation": ", "
                        },
                        {
                            "begin_time": 844,
                            "end_time": 1092,
                            "text": "这",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1092,
                            "end_time": 1340,
                            "text": "里",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1340,
                            "end_time": 1588,
                            "text": "是",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1588,
                            "end_time": 1836,
                            "text": "阿",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 1836,
                            "end_time": 2084,
                            "text": "里",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2084,
                            "end_time": 2332,
                            "text": "巴",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2332,
                            "end_time": 2580,
                            "text": "巴",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2580,
                            "end_time": 2828,
                            "text": "语",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 2828,
                            "end_time": 3076,
                            "text": "音",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 3076,
                            "end_time": 3324,
                            "text": "实",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 3324,
                            "end_time": 3572,
                            "text": "验",
                            "punctuation": ""
                        },
                        {
                            "begin_time": 3572,
                            "end_time": 3820,
                            "text": "室",
                            "punctuation": "。"
                        }
                    ]
                }
            ]
        }
    ]
}
```

## SenseVoice

由于音视频文件的尺寸通常较大，文件传输和语音识别处理均需要时间，文件转写 API 通过异步调用方式来提交任务。开发者需要通过查询接口，在文件转写完成后获得语音识别结果。

Python

```python
# For prerequisites running the following sample, visit https://help.aliyun.com/document_detail/611472.html

import re
import json
from urllib import request
from http import HTTPStatus
import os
import dashscope

# 获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY')

def parse_sensevoice_result(data, keep_trans=True, keep_emotions=True, keep_events=True):
    '''
    本工具用于解析 sensevoice 识别结果
    keep_trans: 是否保留转写文本，默认为True
    keep_emotions: 是否保留情感标签，默认为True
    keep_events: 是否保留事件标签，默认为True
    '''
    # 定义要保留的标签
    emotion_list = ['NEUTRAL', 'HAPPY', 'ANGRY', 'SAD']
    event_list = ['Speech', 'Applause', 'BGM', 'Laughter']

    # 所有支持的标签
    all_tags = ['Speech', 'Applause', 'BGM', 'Laughter',
                'NEUTRAL', 'HAPPY', 'ANGRY', 'SAD', 'SPECIAL_TOKEN_1']
    tags_to_cleanup = []
    for tag in all_tags:
        tags_to_cleanup.append(f'<|{tag}|> ')
        tags_to_cleanup.append(f'<|/{tag}|>')
        tags_to_cleanup.append(f'<|{tag}|>')

    def get_clean_text(text: str):
        for tag in tags_to_cleanup:
            text = text.replace(tag, '')
        pattern = r"\s{2,}"
        text = re.sub(pattern, " ", text).strip()
        return text

    for item in data['transcripts']:
        for sentence in item['sentences']:
            if keep_emotions:
                # 提取 emotion
                emotions_pattern = r'<\|(' + '|'.join(emotion_list) + r')\|>'
                emotions = re.findall(emotions_pattern, sentence['text'])
                sentence['emotion'] = list(set(emotions))
                if not sentence['emotion']:
                    sentence.pop('emotion', None)

            if keep_events:
                # 提取 event
                events_pattern = r'<\|(' + '|'.join(event_list) + r')\|>'
                events = re.findall(events_pattern, sentence['text'])
                sentence['event'] = list(set(events))
                if not sentence['event']:
                    sentence.pop('event', None)

            if keep_trans:
                # 提取纯文本
                sentence['text'] = get_clean_text(sentence['text'])
            else:
                sentence.pop('text', None)

        if keep_trans:
            item['text'] = get_clean_text(item['text'])
        else:
            item.pop('text', None)
        item['sentences'] = list(filter(lambda x: 'text' in x or 'emotion' in x or 'event' in x, item['sentences']))
    return data

task_response = dashscope.audio.asr.Transcription.async_call(
    model='sensevoice-v1',
    file_urls=[
        'https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/sensevoice/rich_text_example_1.wav'],
    language_hints=['en'], ) # language_hints为可选参数，用于指定待识别音频的语言代码。取值范围请参见API参考文档。

print('task_id: ', task_response.output.task_id)

transcription_response = dashscope.audio.asr.Transcription.wait(
    task=task_response.output.task_id)

if transcription_response.status_code == HTTPStatus.OK:
    for transcription in transcription_response.output['results']:
        if transcription['subtask_status'] == 'SUCCEEDED':
            url = transcription['transcription_url']
            result = json.loads(request.urlopen(url).read().decode('utf8'))
            print(json.dumps(parse_sensevoice_result(result, keep_trans=False, keep_emotions=False), indent=4,
                            ensure_ascii=False))
        else:
            print('transcription failed!')
            print(transcription)
    print('transcription done!')
else:
    print('Error: ', transcription_response.output.message)
```

Java

```java
package org.example.recognition;

import com.alibaba.dashscope.audio.asr.transcription.*;
import com.google.gson.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;

class SenseVoiceParser {

    private static final List<String> EMOTION_LIST = Arrays.asList("NEUTRAL", "HAPPY", "ANGRY", "SAD");
    private static final List<String> EVENT_LIST = Arrays.asList("Speech", "Applause", "BGM", "Laughter");
    private static final List<String> ALL_TAGS = Arrays.asList(
            "Speech", "Applause", "BGM", "Laughter", "NEUTRAL", "HAPPY", "ANGRY", "SAD", "SPECIAL_TOKEN_1");

    /**
     * 本工具用于解析 sensevoice 识别结果
     * @param data json格式的sensevoice转写结果
     * @param keepTrans 是否保留转写文本
     * @param keepEmotions 是否保留情感标签
     * @param keepEvents 是否保留事件标签
     * @return
     */
    public static JsonObject parseSenseVoiceResult(JsonObject data, boolean keepTrans, boolean keepEmotions, boolean keepEvents) {

        List<String> tagsToCleanup = ALL_TAGS.stream()
                .flatMap(tag -> Stream.of("<|" + tag + "|> ", "<|/" + tag + "|>", "<|" + tag + "|>"))
                .collect(Collectors.toList());

        JsonArray transcripts = data.getAsJsonArray("transcripts");

        for (JsonElement transcriptElement : transcripts) {
            JsonObject transcript = transcriptElement.getAsJsonObject();
            JsonArray sentences = transcript.getAsJsonArray("sentences");

            for (JsonElement sentenceElement : sentences) {
                JsonObject sentence = sentenceElement.getAsJsonObject();
                String text = sentence.get("text").getAsString();

                if (keepEmotions) {
                    extractTags(sentence, text, EMOTION_LIST, "emotion");
                }

                if (keepEvents) {
                    extractTags(sentence, text, EVENT_LIST, "event");
                }

                if (keepTrans) {
                    String cleanText = getCleanText(text, tagsToCleanup);
                    sentence.addProperty("text", cleanText);
                } else {
                    sentence.remove("text");
                }
            }

            if (keepTrans) {
                transcript.addProperty("text", getCleanText(transcript.get("text").getAsString(), tagsToCleanup));
            } else {
                transcript.remove("text");
            }

            JsonArray filteredSentences = new JsonArray();
            for (JsonElement sentenceElement : sentences) {
                JsonObject sentence = sentenceElement.getAsJsonObject();
                if (sentence.has("text") || sentence.has("emotion") || sentence.has("event")) {
                    filteredSentences.add(sentence);
                }
            }
            transcript.add("sentences", filteredSentences);
        }
        return data;
    }

    private static void extractTags(JsonObject sentence, String text, List<String> tagList, String key) {
        String pattern = "<\\|(" + String.join("|", tagList) + ")\\|>";
        Pattern compiledPattern = Pattern.compile(pattern);
        Matcher matcher = compiledPattern.matcher(text);
        Set<String> tags = new HashSet<>();

        while (matcher.find()) {
            tags.add(matcher.group(1));
        }

        if (!tags.isEmpty()) {
            JsonArray tagArray = new JsonArray();
            tags.forEach(tagArray::add);
            sentence.add(key, tagArray);
        } else {
            sentence.remove(key);
        }
    }

    private static String getCleanText(String text, List<String> tagsToCleanup) {
        for (String tag : tagsToCleanup) {
            text = text.replace(tag, "");
        }
        return text.replaceAll("\\s{2,}", " ").trim();
    }
}

public class Main {
    public static void main(String[] args) {
        // 创建转写请求参数，需要用真实apikey替换your-dashscope-api-key
        TranscriptionParam param =
                TranscriptionParam.builder()
                        // 获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
                        // 若没有配置环境变量，请用百炼API Key将下行替换为：.apiKey("sk-xxx")
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .model("sensevoice-v1")
                        .fileUrls(
                                Arrays.asList(
                                        "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/sensevoice/rich_text_example_1.wav"))
                        // language_hints为可选参数，用于指定待识别音频的语言代码。取值范围请参见API参考文档。
                        .parameter("language_hints", new String[] {"en"})
                        .build();
        try {
            Transcription transcription = new Transcription();
            // 提交转写请求
            TranscriptionResult result = transcription.asyncCall(param);
            System.out.println("requestId: " + result.getRequestId());
            // 等待转写完成
            result = transcription.wait(
                    TranscriptionQueryParam.FromTranscriptionParam(param, result.getTaskId()));
            // 获取转写结果
            List<TranscriptionTaskResult> taskResultList = result.getResults();
            if (taskResultList != null && taskResultList.size() > 0) {
                for (TranscriptionTaskResult taskResult : taskResultList) {
                    String transcriptionUrl = taskResult.getTranscriptionUrl();
                    HttpURLConnection connection =
                            (HttpURLConnection) new URL(transcriptionUrl).openConnection();
                    connection.setRequestMethod("GET");
                    connection.connect();
                    BufferedReader reader =
                            new BufferedReader(new InputStreamReader(connection.getInputStream()));
                    Gson gson = new GsonBuilder().setPrettyPrinting().create();
                    JsonElement jsonResult = gson.fromJson(reader, JsonObject.class);
                    System.out.println(gson.toJson(jsonResult));
                    System.out.println(gson.toJson(SenseVoiceParser.parseSenseVoiceResult(jsonResult.getAsJsonObject(), true, true, true)));
                }
            }
        } catch (Exception e) {
            System.out.println("error: " + e);
        }
        System.exit(0);
    }
}
```

完整的识别结果会以 JSON 格式打印在控制台。完整结果包含转换后的文本以及文本在音视频文件中的起始、结束时间（以毫秒为单位）。本示例中，还检测到了说话声事件（`<|Speech|>` 与`<|/Speech|>` 分别代表说话声事件的起始与结束），情绪（`<|ANGRY|>` ）。

```json
{
    "file_url": "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/sensevoice/rich_text_example_1.wav",
    "properties": {
        "audio_format": "pcm_s16le",
        "channels": [
            0
        ],
        "original_sampling_rate": 16000,
        "original_duration_in_milliseconds": 17645
    },
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 12710,
            "text": "<|Speech|> Senior staff, Principal Doris Jackson, Wakefield faculty, and of course, my fellow classmates. <|/Speech|> <|ANGRY|><|Speech|> I am honored to have been chosen to speak before my classmates, as well as the students across America today. <|/Speech|>",
            "sentences": [
                {
                    "begin_time": 0,
                    "end_time": 7060,
                    "text": "<|Speech|> Senior staff, Principal Doris Jackson, Wakefield faculty, and of course, my fellow classmates. <|/Speech|> <|ANGRY|>"
                },
                {
                    "begin_time": 11980,
                    "end_time": 17630,
                    "text": "<|Speech|> I am honored to have been chosen to speak before my classmates, as well as the students across America today. <|/Speech|>"
                }
            ]
        }
    ]
}
```

## ** API 参考**

- [Fun-ASR录音文件识别API参考](https://help.aliyun.com/zh/model-studio/fun-asr-recorded-speech-recognition-api-reference/)

- [Paraformer录音文件识别API参考](https://help.aliyun.com/zh/model-studio/paraformer-recorded-speech-recognition-api-reference/)

- [SenseVoice录音文件识别API参考](https://help.aliyun.com/zh/model-studio/sensevoice-speech-recognition/)

## ** 模型应用上架及备案**

参见[应用合规备案](https://help.aliyun.com/zh/model-studio/compliance-and-launch-filing-guide-for-ai-apps-powered-by-the-tongyi-model) 。

## ** 模型功能特性对比**

<table id="5c74ba8bc177u" tablewidth="100" tablecolswidth="12.85 26.64 31.06 29.450000000000003" autofit="true" class="table"><colgroup colwidth="0.51*" style="width:12.85%"></colgroup><colgroup colwidth="1.07*" style="width:26.64%"></colgroup><colgroup colwidth="1.24*" style="width:31.06%"></colgroup><colgroup colwidth="1.18*" style="width:29.45%"></colgroup><tbody class="tbody"><tr id="aa0c5026f521w"><td id="8b72d74af11wl" rowspan="1" style="background-color:#e5e5e5;vertical-align:middle" colspan="1"><p jc="left" id="81aa0bd488177" style="text-align:left"><b>功能/特性</b></p></td><td id="e0f7078aa5t2v" rowspan="1" style="background-color:#e5e5e5" colspan="1"><p id="486dec6aa655q"><b>Fun-ASR</b></p></td><td id="a4bc426cca41a" rowspan="1" style="background-color:#e5e5e5;vertical-align:middle" colspan="1"><p jc="left" id="a8f5f862d6c52" style="text-align:left"><b>Paraformer</b></p></td><td id="16ab4593ddlu1" rowspan="1" style="background-color:#e5e5e5;vertical-align:middle" colspan="1"><p jc="left" id="355624cd3drua" style="text-align:left"><span style="color:rgb(0, 0, 0)"><b>SenseVoice（即将下线）</b></span></p></td></tr><tr id="ed1846a6813l3"><td id="bb1356fe5cw63" rowspan="1" style="vertical-align:middle" colspan="1"><p jc="left" id="0a22a057bdvqz" style="text-align:left"><b>支持语言</b></p></td><td id="b3f7143e089pg" rowspan="1" colspan="1"><p id="2e798e99b9fzc">因模型而异：</p><ul id="5fe26e557c41r"><li id="9cbfe698bcgj9"><p id="c9d2bd348disp">fun-asr、fun-asr-2025-11-07：</p><section id="be88ee885by4z" docid="6040295" is-conref="true" class="section"><p id="afc58f0563eb1">中文（普通话、粤语、吴语、闽南语、客家话、赣语、湘语、晋语；并支持中原、西南、冀鲁、江淮、兰银、胶辽、东北、北京、港台等，包括河南、陕西、湖北、四川、重庆、云南、贵州、广东、广西、河北、天津、山东、安徽、南京、江苏、杭州、甘肃、宁夏等地区官话口音）、英文、日语</p></section></li><li id="9945713481egz"><p id="224ec55625c4w">fun-asr-2025-08-25：</p><section id="c9726d7906gaw" docid="6040295" is-conref="true" class="section"><p id="4dab1b2aeax24">中文（普通话）、英文</p></section></li><li id="2f906458558pr"><p id="5625a606c1yey">fun-asr-mtl、fun-asr-mtl-2025-08-25：</p><section id="ff809a8858n5l" docid="6040295" is-conref="true" class="section"><p id="6373dfe63fr60">中文（普通话、粤语）、英文、日语、韩语、越南语、印尼语、泰语、马来语、菲律宾语、阿拉伯语、印地语、保加利亚语、克罗地亚语、捷克语、丹麦语、荷兰语、爱沙尼亚语、芬兰语、希腊语、匈牙利语、爱尔兰语、拉脱维亚语、立陶宛语、马耳他语、波兰语、葡萄牙语、罗马尼亚语、斯洛伐克语、斯洛文尼亚语、瑞典语</p></section></li></ul></td><td id="a9df72913cshn" rowspan="1" colspan="1"><p id="1e76a0e28fk15">因模型而异：</p><ul id="aadb6cd2e0un6"><li id="c6ab1d24bfh9w"><p id="ae04e38a788fs">paraformer-v2：</p><section id="7d27073877jp9" docid="6040295" is-conref="true" class="section"><p id="1b82d45ed0a5f">中文（普通话、粤语、吴语、闽南语、东北话、甘肃话、贵州话、河南话、湖北话、湖南话、宁夏话、山西话、陕西话、山东话、四川话、天津话、江西话、云南话、上海话）、英文、日语、韩语、德语、法语、俄语</p></section></li><li id="7e225df861t72"><p id="7e7f7631cd7if">paraformer-8k-v2：中文普通话</p></li><li id="70ac5a656e4jf"><p id="01b0e16748i0e">paraformer-v1：中文普通话、英文</p></li><li id="37ccf3f445upz"><p id="e34ceab772h5y">paraformer-8k-v1：中文普通话</p></li><li id="1fb316b648igb"><p id="9b2f8533c99re">paraformer-mtl-v1：中文（普通话、粤语、吴语、闽南语、东北话、甘肃话、贵州话、河南话、湖北话、湖南话、宁夏话、山西话、陕西话、山东话、四川话、天津话）、英文、日语、韩语、西班牙语、印尼语、法语、德语、意大利语、马来语</p></li></ul></td><td id="21a5aa2029ae9" rowspan="1" style="vertical-align:middle" colspan="1"><ul id="c758ed7a2b7py"><li id="655ae06ef4hyl"><p id="3c95139931cpq">重点语言：中文、英文、粤语、日语、韩语、俄语、法语、意大利语、德语、西班牙语</p></li><li id="73d20f4413qes"><p id="90bf0f459cvhy">更多语言：加泰罗尼亚语、印度尼西亚语、泰语、荷兰语、葡萄牙语、捷克语、波兰语等，详情请参见<a href="https://help.aliyun.com/zh/model-studio/sensevoice-recorded-speech-recognition-java-sdk#7a65158a77hpf" id="f0c02864b8rff" title="" class="xref">语言列表</a></p></li></ul></td></tr><tr id="5836bcd5c1p9w"><td id="a157bcd4aa8i7" rowspan="1" style="vertical-align:middle" colspan="1"><p id="9cf148494cbbd"><b>支持的音频格式</b></p></td><td id="75f44b9fa5uw5" rowspan="1" colspan="1"><section id="aef4881f1akco" docid="6040295" is-conref="true" class="section"><p id="4150b8b785ax8">aac、amr、avi、flac、flv、m4a、mkv、mov、mp3、mp4、mpeg、ogg、opus、wav、webm、wma、wmv</p></section></td><td id="daf9287c5596r" rowspan="1" style="vertical-align:middle" colspan="1"><p jc="left" id="443fa8e6ab94w" style="text-align:left">aac、amr、avi、flac、flv、m4a、mkv、mov、mp3、mp4、mpeg、ogg、opus、wav、webm、wma、wmv</p></td><td id="1d7cd0def7dv8" rowspan="1" colspan="1"><p id="e32ac15ab44s1">aac、amr、avi、flac、flv、m4a、mkv、mov、mp3、mp4、mpeg、ogg、opus、wav、webm、wma、wmv</p></td></tr><tr id="b65131019f9fh"><td id="16fbfa7208o5e" rowspan="1" style="vertical-align:middle" colspan="1"><p jc="left" id="0aeeda69afn6v" style="text-align:left"><b>采样率</b></p></td><td id="4626e09eb28dj" rowspan="1" colspan="1"><p id="e78a8118702uj">任意</p></td><td id="f8aefb0b5d0ob" rowspan="1" colspan="1"><p id="42afec358eapo">因模型而异：</p><ul id="bb9cbbbae1btt"><li id="3b96cfa2ae05i"><p id="74d8294a46umf">paraformer-v2、paraformer-v1：任意</p></li><li id="a0907c4359vvo"><p id="6eaf90b4de6sa">paraformer-8k-v2、paraformer-8k-v1：8kHz</p></li><li id="2de5bfb879364"><p id="ffd41b0f8adtu">paraformer-mtl-v1：16kHz<span class="help-letter-space"></span>及以上</p></li></ul></td><td id="f310a492d4qkx" rowspan="1" colspan="1"><p id="53c4791f114c4">任意</p></td></tr><tr id="b631d7f7b3pg6"><td id="772427a09ch61" rowspan="1" style="vertical-align:middle" colspan="1"><p id="7488f0efd5cgt"><b>声道</b></p></td><td id="4a958a3e6affr" rowspan="1" colspan="3"><p id="77f658abe52v1">任意</p></td></tr><tr id="9be4c69a7bbj6"><td id="c284882a3e1y3" rowspan="1" style="vertical-align:middle" colspan="1"><p id="a7b96b02d0e1t"><b>输入形式</b></p></td><td id="459725b8bbesa" rowspan="1" colspan="3"><p id="b4df1913d4u2u">公网可访问的待识别文件<span class="help-letter-space"></span>URL，最多支持输入<span class="help-letter-space"></span>100<span class="help-letter-space"></span>个音频</p></td></tr><tr id="b0aec3c5b8fdl"><td id="04b8820dde2t9" rowspan="1" style="vertical-align:middle" colspan="1"><p id="271db0aa18d1k"><b>音频大小/时长</b></p></td><td id="0fa5eaec66x9f" rowspan="1" colspan="2"><p id="875d8f38b84xf">每个音频文件大小不超过<span class="help-letter-space"></span>2GB，且时长不超过<span class="help-letter-space"></span>12<span class="help-letter-space"></span>小时</p></td><td id="f047aefdecknj" rowspan="1" colspan="1"><p id="b1b3e5027eoe7">每个音频文件大小不超过<span class="help-letter-space"></span>2GB，时长无限制</p></td></tr><tr id="79b17864b3n4n"><td id="7f1ab2a55b3hx" rowspan="1" style="vertical-align:middle" colspan="1"><p id="107918cd90rae"><b>情感识别</b></p></td><td id="f582c7e430jdh" rowspan="1" colspan="2"><p id="58f3e04eb74f4"><span data-tag="ph" id="0f9f5cc64b7vv" outputclass="aliyun-docs-icon-close aliyun-docs-icon" data-ref-searchable="yes" docid="5715676" data-init-id="1282d783e3wbz" is-conref="true" class="ph aliyun-docs-icon-close aliyun-docs-icon">不支持</span></p></td><td id="08ae9cb3f2emj" rowspan="1" style="vertical-align:middle" colspan="1"><p id="4848603d32m1l"><span data-tag="ph" id="45bad6deffnvi" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">固定开启</span></p></td></tr><tr id="7ccac6ae8bvub"><td id="e5eca441371pl" rowspan="1" style="vertical-align:middle" colspan="1"><p id="05f6761ae2mom"><b>时间戳</b></p></td><td id="1aa5f89d8657n" rowspan="1" colspan="1"><p id="38adae2abai1l"><span data-tag="ph" id="a44e7e98edm12" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">固定开启</span></p></td><td id="b3b30aea446o4" rowspan="1" style="vertical-align:middle" colspan="1"><p id="4db1901cd782f"><span data-tag="ph" id="90df56b884lrj" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">默认关闭，可开启</span></p></td><td id="84e8bb883e7iy" rowspan="1" colspan="1"><p id="32edfb2374bj2"><span data-tag="ph" id="2971fd8f7bb2a" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">固定开启</span></p></td></tr><tr id="bf2e3f24ceghe"><td id="f7c3aa58bal21" rowspan="1" style="vertical-align:middle" colspan="1"><p id="161e8fb9f71wp"><b>标点符号预测</b></p></td><td id="5a9a8a4cbdx30" rowspan="1" colspan="3"><p id="404cba3fd0xkm"><span data-tag="ph" id="9f29f7bef6ihb" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">固定开启</span></p></td></tr><tr id="24f60795abjbe"><td id="901dde66ec87v" rowspan="1" style="vertical-align:middle" colspan="1"><p id="e21136c41443y"><b>热词</b></p></td><td id="e14bde410ftnj" rowspan="1" colspan="2"><p id="24bd5cbf5cfqb"><span data-tag="ph" id="62626b2ec7uvt" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" comment_2138ad30-3d0b-48df-abce-c964beff2054="comment" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">可配置</span></p></td><td id="8ba6cb8cde0ub" rowspan="1" style="vertical-align:middle" colspan="1"><p id="0387da17c79t4"><span data-tag="ph" id="25735018bf824" outputclass="aliyun-docs-icon-close aliyun-docs-icon" data-ref-searchable="yes" docid="5715676" data-init-id="1282d783e3wbz" is-conref="true" class="ph aliyun-docs-icon-close aliyun-docs-icon">不支持</span></p></td></tr><tr id="567ce812ebb1u"><td id="4cbc01200b804" rowspan="1" style="vertical-align:middle" colspan="1"><p id="2d78d30aef3tx"><b>ITN</b></p></td><td id="8a7938e600nxv" rowspan="1" colspan="3"><p id="b6d8513cf8izk"><span data-tag="ph" id="6a8174a7c7vof" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">固定开启</span></p></td></tr><tr id="88af3a5a24zth"><td id="3ac388559b3r3" rowspan="1" colspan="1"><p id="0858015a3e1gd"><b>歌唱识别</b></p></td><td id="512eb42b25hzf" rowspan="1" colspan="1"><p id="f64c34871ak2q"><span data-tag="ph" id="0057b09cf2ohl" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> 仅<span class="help-letter-space"></span>fun-asr<span class="help-letter-space"></span>和<span class="help-letter-space"></span>fun-asr-2025-11-07<span class="help-letter-space"></span>支持该功能</p></td><td id="e92c93287cg1h" rowspan="1" colspan="2"><p id="f2dab7e6b5k6n"><span data-tag="ph" id="74817d428bn4j" outputclass="aliyun-docs-icon-close aliyun-docs-icon" data-ref-searchable="yes" docid="5715676" data-init-id="1282d783e3wbz" is-conref="true" class="ph aliyun-docs-icon-close aliyun-docs-icon">不支持</span></p></td></tr><tr id="681d78dbfffh4"><td id="a01af2a30drlz" rowspan="1" colspan="1"><p id="dc8587abecu7t"><b>噪声拒识</b></p></td><td id="e8cbbbfe8dlp0" rowspan="1" colspan="2"><p id="35bd51260dg8o"><span data-tag="ph" id="a4020fc695org" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">固定开启</span></p></td><td id="acb184e3c6w6m" rowspan="1" colspan="1"><p id="3bdfaa962a78e"><span data-tag="ph" id="bcdd24b2e7sdx" outputclass="aliyun-docs-icon-close aliyun-docs-icon" data-ref-searchable="yes" docid="5715676" data-init-id="1282d783e3wbz" is-conref="true" class="ph aliyun-docs-icon-close aliyun-docs-icon">不支持</span></p></td></tr><tr id="cd59387723cqz"><td id="3312d50402916" rowspan="1" style="vertical-align:middle" colspan="1"><p id="7dd227f586x9b"><b>敏感词过滤</b></p></td><td id="17a974c6b6yew" rowspan="1" style="vertical-align:middle" colspan="2"><p id="c9b5603f66qnx"><span data-tag="ph" id="d5f54533dfxif" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">默认过滤</span><a href="https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/%E7%99%BE%E7%82%BC%E6%95%8F%E6%84%9F%E8%AF%8D%E5%88%97%E8%A1%A8_20230716.words.txt" id="dab988b2c0iwo" class="" target="_blank">阿里云百炼敏感词表</a>中的内容，更多内容过滤需自定义</p></td><td id="1fadae3d7djix" rowspan="1" colspan="1"><p id="c3715cfbe0h55"><span data-tag="ph" id="cbafd60d41583" outputclass="aliyun-docs-icon-close aliyun-docs-icon" data-ref-searchable="yes" docid="5715676" data-init-id="1282d783e3wbz" is-conref="true" class="ph aliyun-docs-icon-close aliyun-docs-icon">不支持</span></p></td></tr><tr id="233eb6cabf43t"><td id="d03c6017738x9" rowspan="1" style="vertical-align:middle" colspan="1"><p id="640df19e68jsf"><b>说话人分离</b></p></td><td id="a5f846c933ia6" rowspan="1" style="vertical-align:middle" colspan="2"><p id="41f24932deqn6"><span data-tag="ph" id="a1bd7625ecls9" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> 默认关闭，可开启</p></td><td id="d80df1eefb9e7" rowspan="1" colspan="1"><p id="8839efa629fdn"><span data-tag="ph" id="909fc66c71bm2" outputclass="aliyun-docs-icon-close aliyun-docs-icon" data-ref-searchable="yes" docid="5715676" data-init-id="1282d783e3wbz" is-conref="true" class="ph aliyun-docs-icon-close aliyun-docs-icon">不支持</span></p></td></tr><tr id="2f13277147tqz"><td id="aafd22786abrw" rowspan="1" style="vertical-align:middle" colspan="1"><p id="b3dcf7d69fna9"><b>语气词过滤</b></p></td><td id="9ea3289d18wdt" rowspan="1" style="vertical-align:middle" colspan="2"><p id="de7786ef15szw"><span data-tag="ph" id="a5ffa5eb16obv" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> 默认关闭，可开启</p></td><td id="e6e3d27b68n9b" rowspan="1" style="vertical-align:middle" colspan="1"><p id="0be716f34bymi"><span data-tag="ph" id="ede49d5fd5m9k" outputclass="aliyun-docs-icon-close aliyun-docs-icon" data-ref-searchable="yes" docid="5715676" data-init-id="1282d783e3wbz" is-conref="true" class="ph aliyun-docs-icon-close aliyun-docs-icon">不支持</span></p></td></tr><tr id="356bd238698r7"><td id="ac1e12dbf6631" rowspan="1" style="vertical-align:middle" colspan="1"><p id="8eb68328c6xjf"><b>VAD</b></p></td><td id="162ebf98ca3rh" rowspan="1" style="vertical-align:middle" colspan="2"><p id="494cdc4ed3ycy"><span data-tag="ph" id="73eccae07a5hm" outputclass="aliyun-docs-icon-check_fill aliyun-docs-icon" data-ref-searchable="yes" docid="5715677" data-init-id="4ffedea1f50yx" is-conref="true" class="aliyun-docs-icon-check_fill aliyun-docs-icon ph">支持</span> <span style="color:rgb(24, 24, 24)">固定开启</span></p></td><td id="026049ac2c2e2" rowspan="1" colspan="1"><p id="1e92a0853aigs"><span data-tag="ph" id="12b68c359bao4" outputclass="aliyun-docs-icon-close aliyun-docs-icon" data-ref-searchable="yes" docid="5715676" data-init-id="1282d783e3wbz" is-conref="true" class="ph aliyun-docs-icon-close aliyun-docs-icon">不支持</span></p></td></tr><tr id="afb63a91b9pyp"><td id="f4326d5ae1bqr" rowspan="1" style="vertical-align:middle" colspan="1"><p id="83b1a8481283a"><b>限流（RPS）</b></p></td><td id="427e6c9287k71" rowspan="1" colspan="1"><p id="49f86f17343sw">提交作业接口：10</p><p id="57bf6a7f7beu6">任务查询接口：20</p></td><td id="c04e372b7ebmp" rowspan="1" colspan="1"><p id="83605a715cgkl">提交作业接口（因模型而异）：</p><ul id="b590c3cf50eag"><li id="d1c56f3cdam6s"><p id="b2511238daw7k">paraformer-v2、paraformer-8k-v2：20</p></li><li id="112305c3e2fca"><p id="9650010469ivr">paraformer-v1、paraformer-8k-v1、paraformer-mtl-v1：10</p></li></ul><p id="ac42fb49d87n2">任务查询接口：20</p></td><td id="13ef2e84b3890" rowspan="1" colspan="1"><p id="7c1774ea7blmw">提交作业接口：10</p><p id="be7e04f10baco">任务查询接口：20</p></td></tr><tr id="04b670daa5y23"><td id="ae3050686725a" rowspan="1" style="vertical-align:middle" colspan="1"><p id="871e507cddp0z"><b>接入方式</b></p></td><td id="ed52b5e829fao" rowspan="1" colspan="2"><p id="3ae4366cf4iti">DashScope：Java/Python/Android/iOS SDK、RESTful API</p></td><td id="299dec9c03io7" rowspan="1" colspan="1"><p id="d2566b0c93d8j">DashScope：Java/Python SDK、RESTful API</p></td></tr><tr id="ceec5ffe9cg58"><td id="7ddd4d3a6ffqy" rowspan="1" style="vertical-align:middle" colspan="1"><p id="c868de5ac9cyv"><b>价格</b></p></td><td id="9f38e7da693hd" rowspan="1" colspan="1"><p id="697d600182ghp">中国内地：0.00022<span class="help-letter-space"></span>元/秒</p><p id="e27bd83b02vbw">国际：0.00026<span class="help-letter-space"></span>元/秒</p></td><td id="450d26f312h74" rowspan="1" colspan="1"><p id="05f0fdc3e3b8q">中国内地：0.00008<span class="help-letter-space"></span>元/秒</p></td><td id="a3305a770b3zx" rowspan="1" style="vertical-align:middle" colspan="1"><p jc="left" id="71cdbf2d4bfi9" style="text-align:left">中国内地：0.0007 元/秒</p></td></tr></tbody></table>

## 常见问题

### ** Q：如何提升识别准确率？**

需综合考虑影响因素并采取相应措施。

主要影响因素：

1. 声音质量：录音设备、采样率及环境噪声影响清晰度（高质量音频是基础）

2. 说话人特征：音调、语速、口音和方言差异（尤其少见方言或重口音）增加识别难度

3. 语言和词汇：多语言混合、专业术语或俚语提升识别难度（热词配置可优化）

4. 上下文理解：缺乏上下文易导致语义歧义（尤其在依赖前后文才能正确识别的语境中）

优化方法：

1. 优化音频质量：使用高性能麦克风及推荐采样率设备；减少环境噪声与回声

2. 适配说话人：针对显著口音/方言场景，选用支持方言的模型

3. 配置热词：为专业术语、专有名词等设置热词（参见[定制热词](https://help.aliyun.com/zh/model-studio/custom-hot-words) ）

4. 保留上下文：避免过短音频分段

**[上一篇：实时语音识别-通义千问](https://help.aliyun.com/zh/model-studio/qwen-real-time-speech-recognition)**[下一篇：录音文件识别-通义千问](https://help.aliyun.com/zh/model-studio/qwen-speech-recognition) 该文章对您有帮助吗？
