package com.bossair.app.domain.model

import java.util.UUID

/**
 * 录音会话
 */
data class RecordingSession(
    val id: String = UUID.randomUUID().toString(),
    val startTime: Long = System.currentTimeMillis(),
    val endTime: Long? = null,
    val duration: Long = 0,
    val status: RecordingStatus = RecordingStatus.IDLE,
    val scenario: String = "商务谈判",
    val transcript: List<TranscriptSegment> = emptyList(),
    val alerts: List<AlertEvent> = emptyList(),
    val products: List<SessionProduct> = emptyList()
)

enum class RecordingStatus {
    IDLE, RECORDING, PAUSED, STOPPED, PROCESSING, ERROR
}

data class TranscriptSegment(
    val id: String = UUID.randomUUID().toString(),
    val sessionId: String,
    val speakerId: String,
    val speakerName: String,
    val text: String,
    val startTime: Long,
    val endTime: Long,
    val confidence: Float = 0f,
    val isFinal: Boolean = false
)

data class AlertEvent(
    val id: String = UUID.randomUUID().toString(),
    val sessionId: String,
    val type: AlertType,
    val priority: AlertPriority,
    val content: String,
    val evidence: String,
    val timestamp: Long = System.currentTimeMillis(),
    val confidence: Float = 0f,
    val deliveredChannels: List<String> = emptyList()
)

enum class AlertType {
    KEYWORD_ALERT, EMOTION_SIGNAL, RISK, OPPORTUNITY, INTERJECTION_SUGGEST, PERIODIC_SUMMARY
}

enum class AlertPriority {
    HIGH, MEDIUM, LOW
}

data class SessionProduct(
    val id: String = UUID.randomUUID().toString(),
    val sessionId: String,
    val type: ProductType,
    val title: String,
    val content: String,
    val source: String = "",
    val createdAt: Long = System.currentTimeMillis()
)

enum class ProductType {
    MINUTES, OPPORTUNITY, TODO, DECISION_CARD, REVIEW
}
